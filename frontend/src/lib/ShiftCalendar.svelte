<script>
  import { onMount } from 'svelte'
  import { scheduleResult, warnings, loading, errorMsg, members, ngEntries, scheduleView } from './store.js'
  import { api } from './api.js'

  /** 当番統計ページへ（親から渡す） */
  export let onOpenStats = () => {}

  const DAY_LABELS = ['月', '火', '水', '木', '金', '土', '日']
  // config/settings.yaml の schedule.night_shift_start_weekday（0=月）に合わせる
  const NIGHT_WEEK_START_PY_WEEKDAY = 0

  let startDate = ''
  let endDate = ''
  let nextHistory = []
  let referenceHistoryState = null
  let nextHistoryState = null
  /** 表示・編集用（生成直後＝スナップショット） */
  let localEntries = null
  let lastNextHistoryForExport = null
  let snapshotEntries = null

  function addDays(dateStr, days) {
    const d = new Date(`${dateStr}T00:00:00`)
    d.setDate(d.getDate() + days)
    return d.toISOString().slice(0, 10)
  }

  // デフォルト: 今週月曜〜日曜
  const today = new Date()
  const dayOfWeek = today.getDay() // 0=日
  const monday = new Date(today)
  monday.setDate(today.getDate() - ((dayOfWeek + 6) % 7))
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  startDate = monday.toISOString().slice(0, 10)
  endDate = sunday.toISOString().slice(0, 10)

  function toPyWeekday(dateStr) {
    const d = new Date(`${dateStr}T12:00:00`)
    return (d.getDay() + 6) % 7
  }

  function weekStartDateStr(dateStr, startWeekdayPy) {
    const d = new Date(`${dateStr}T12:00:00`)
    const pywd = toPyWeekday(dateStr)
    const back = (pywd - startWeekdayPy + 7) % 7
    d.setDate(d.getDate() - back)
    return d.toISOString().slice(0, 10)
  }

  function dateOf(e) {
    if (!e || e.date == null) return ''
    if (typeof e.date === 'string') return e.date
    if (e.date && typeof e.date === 'object' && typeof e.date.toISOString === 'function') {
      return e.date.toISOString().slice(0, 10)
    }
    return String(e.date).slice(0, 10)
  }

  function slotKey(e) {
    return `${dateOf(e)}|${e.shift_category}|${e.shift_index}`
  }

  function ngInfo(personName, dateStr) {
    if (!dateStr) return { violation: false, reason: '', global: false }
    for (const ng of $ngEntries) {
      const a = ng.start_date
      const b = ng.end_date
      if (dateStr >= a && dateStr <= b) {
        if (ng.person_name == null) {
          return { violation: true, reason: ng.reason || '全体不可', global: true }
        }
        if (ng.person_name === personName) {
          return { violation: true, reason: ng.reason || '当番NG', global: false }
        }
      }
    }
    return { violation: false, reason: '', global: false }
  }

  /** その日に「全体不可」が1件以上か（日付行の強調用） */
  function isGlobalNgDay(dateStr) {
    if (!dateStr) return false
    for (const ng of $ngEntries) {
      if (ng.person_name != null) continue
      if (dateStr >= ng.start_date && dateStr <= ng.end_date) return true
    }
    return false
  }

  function rangesOverlap(aStart, aEnd, bStart, bEnd) {
    return aStart <= bEnd && aEnd >= bStart
  }

  /** カレンダー期間 startDate〜endDate と重なる NG（一覧パネル用） */
  function ngEntriesTouchingViewRange(ngs, vStart, vEnd) {
    if (!vStart || !vEnd) return []
    return ngs.filter((ng) => rangesOverlap(ng.start_date, ng.end_date, vStart, vEnd))
  }

  /** 特定の1日にかかる NG 登録（日付欄用） */
  function ngListForDate(dateStr, ngs) {
    if (!dateStr) return []
    return ngs.filter((ng) => dateStr >= ng.start_date && dateStr <= ng.end_date)
  }

  function candidateNames(entry) {
    const list = $members.filter((m) => m.active)
    let fromFlags = list
    if (entry.shift_category === 'Night') {
      fromFlags = list.filter((m) => m.assignable_night)
    } else if (entry.shift_index === 1) {
      fromFlags = list.filter((m) => m.assignable_day1)
    } else {
      fromFlags = list.filter((m) => m.assignable_day2)
    }
    const names = new Set(fromFlags.map((m) => m.name))
    names.add(entry.person_name)
    return [...names].sort((a, b) => a.localeCompare(b, 'ja'))
  }

  function updatePerson(entry, newName) {
    if (!localEntries) return
    const next = [...localEntries]
    const k0 = slotKey(entry)
    if (entry.shift_category === 'Night') {
      const anchor = weekStartDateStr(
        typeof entry.date === 'string' ? entry.date : String(entry.date).slice(0, 10),
        NIGHT_WEEK_START_PY_WEEKDAY
      )
      for (let i = 0; i < next.length; i++) {
        const e = next[i]
        if (e.shift_category !== 'Night') continue
        const d = typeof e.date === 'string' ? e.date : String(e.date).slice(0, 10)
        if (weekStartDateStr(d, NIGHT_WEEK_START_PY_WEEKDAY) === anchor) {
          next[i] = { ...e, person_name: newName }
        }
      }
    } else {
      const ix = next.findIndex((e) => slotKey(e) === k0)
      if (ix >= 0) next[ix] = { ...next[ix], person_name: newName }
    }
    localEntries = next
  }

  function resetLocalEdits() {
    if (snapshotEntries) {
      localEntries = JSON.parse(JSON.stringify(snapshotEntries))
    }
  }

  function buildExportEntries() {
    if (!localEntries) {
      return nextHistory.length > 0 ? nextHistory : $scheduleResult
    }
    if (!lastNextHistoryForExport) {
      return localEntries
    }
    const slotToPerson = new Map(localEntries.map((e) => [slotKey(e), e.person_name]))
    return lastNextHistoryForExport.map((e) => {
      const k = slotKey(e)
      if (slotToPerson.has(k)) {
        return { ...e, person_name: slotToPerson.get(k) }
      }
      return e
    })
  }

  async function generate() {
    loading.set(true)
    errorMsg.set('')
    try {
      const result = await api.generateSchedule({ start_date: startDate, end_date: endDate })
      scheduleResult.set(result.entries)
      warnings.set(result.warnings)
      nextHistory = result.next_history ?? result.entries
      lastNextHistoryForExport = result.next_history
        ? JSON.parse(JSON.stringify(result.next_history))
        : null
      localEntries = result.entries ? JSON.parse(JSON.stringify(result.entries)) : null
      snapshotEntries = localEntries ? JSON.parse(JSON.stringify(localEntries)) : null
      referenceHistoryState = result.reference_history_state ?? referenceHistoryState
      nextHistoryState = result.history_state ?? null
    } catch (e) {
      errorMsg.set(e.message)
    } finally {
      loading.set(false)
    }
  }

  async function exportCsv() {
    try {
      const entries = buildExportEntries()
      const blob = await api.exportEntries(entries)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'next_history.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      errorMsg.set(e.message)
    }
  }

  onMount(async () => {
    const state = await Promise.allSettled([api.getHistoryState(), api.getMembers(), api.getNgEntries()])
    if (state[0].status === 'fulfilled') {
      referenceHistoryState = state[0].value
      if (referenceHistoryState.next_start_date && referenceHistoryState.next_end_date) {
        startDate = referenceHistoryState.next_start_date
        endDate = referenceHistoryState.next_end_date
      } else if (referenceHistoryState.end_date) {
        startDate = addDays(referenceHistoryState.end_date, 1)
        endDate = addDays(referenceHistoryState.end_date, 7)
      }
    } else {
      errorMsg.set(state[0].reason?.message ?? String(state[0].reason))
    }
    if (state[1].status === 'fulfilled') {
      members.set(state[1].value)
    }
    if (state[2].status === 'fulfilled') {
      ngEntries.set(state[2].value)
    }
  })

  function groupByDate(entries) {
    const map = {}
    for (const e of entries) {
      const key = dateOf(e)
      if (!map[key]) map[key] = []
      map[key].push(e)
    }
    return map
  }

  function getDatesInRange(start, end) {
    const dates = []
    const cur = new Date(start)
    const last = new Date(end)
    while (cur <= last) {
      dates.push(cur.toISOString().slice(0, 10))
      cur.setDate(cur.getDate() + 1)
    }
    return dates
  }

  function dayLabel(dateStr) {
    const d = new Date(dateStr)
    return DAY_LABELS[d.getDay() === 0 ? 6 : d.getDay() - 1]
  }

  function isWeekend(dateStr) {
    const d = new Date(dateStr)
    return d.getDay() === 0 || d.getDay() === 6
  }

  function sortedEntries(entries) {
    return [...entries].sort((a, b) => a.shift_category.localeCompare(b.shift_category) || a.shift_index - b.shift_index)
  }

  $: displayList = localEntries ?? $scheduleResult
  $: if (displayList?.length && startDate && endDate) {
    scheduleView.set({ entries: displayList, rangeStart: startDate, rangeEnd: endDate })
  } else if (!displayList?.length) {
    scheduleView.set({ entries: null, rangeStart: '', rangeEnd: '' })
  }
  $: byDate = displayList ? groupByDate(displayList) : {}
  $: ngConflictCount = (() => {
    if (!displayList) return 0
    let n = 0
    for (const e of displayList) {
      if (ngInfo(e.person_name, dateOf(e)).violation) n += 1
    }
    return n
  })()
  $: isDirty =
    localEntries &&
    snapshotEntries &&
    JSON.stringify(localEntries) !== JSON.stringify(snapshotEntries)
  $: ngListInView = ngEntriesTouchingViewRange($ngEntries, startDate, endDate)

  function getMondayOfWeek(dateStr) {
    const d = new Date(`${dateStr}T12:00:00`)
    const back = (d.getDay() + 6) % 7
    d.setDate(d.getDate() - back)
    return d.toISOString().slice(0, 10)
  }

  function getSundayOfWeek(dateStr) {
    const m = new Date(`${getMondayOfWeek(dateStr)}T12:00:00`)
    m.setDate(m.getDate() + 6)
    return m.toISOString().slice(0, 10)
  }

  /** カレンダー表示: 期間を含む週の月〜日（範囲外の日は薄く表示用） */
  $: calendarStart = startDate && endDate ? getMondayOfWeek(startDate) : ''
  $: calendarEnd = startDate && endDate ? getSundayOfWeek(endDate) : ''
  $: calendarDates =
    calendarStart && calendarEnd ? getDatesInRange(calendarStart, calendarEnd) : []
  $: calendarWeeks = (() => {
    const w = []
    for (let i = 0; i < calendarDates.length; i += 7) {
      w.push(calendarDates.slice(i, i + 7))
    }
    return w
  })()

  function inSelectedRange(d) {
    return d && startDate && endDate && d >= startDate && d <= endDate
  }
</script>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />

<div class="space-y-4">
  <!-- コントロールバー -->
  <div class="glass-panel rounded-2xl p-3 sm:p-4 flex flex-wrap items-end gap-3">
    <div class="flex flex-col gap-1">
      <label for="start-date" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">開始日</label>
      <input
        id="start-date"
        type="date"
        bind:value={startDate}
        class="px-3 py-2 rounded-lg text-sm border focus:outline-none focus:ring-2"
        style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7); color: var(--color-on-surface);"
      />
    </div>
    <div class="flex flex-col gap-1">
      <label for="end-date" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">終了日</label>
      <input
        id="end-date"
        type="date"
        bind:value={endDate}
        class="px-3 py-2 rounded-lg text-sm border focus:outline-none focus:ring-2"
        style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7); color: var(--color-on-surface);"
      />
    </div>
    <button
      on:click={generate}
      disabled={$loading}
      class="px-6 py-2.5 rounded-full text-sm font-semibold transition-all hover:opacity-90 active:scale-95 disabled:opacity-50"
      style="background: var(--color-primary); color: var(--color-on-primary);"
    >
      {$loading ? '生成中...' : 'シフト生成'}
    </button>
    {#if displayList}
      {#if isDirty}
        <button
          on:click={resetLocalEdits}
          class="px-5 py-2.5 rounded-full text-sm font-semibold border transition-all hover:bg-white/50"
          style="border-color: var(--color-outline-variant); color: var(--color-on-surface); background: rgba(255,255,255,0.4);"
        >
          編集を元に戻す
        </button>
      {/if}
      <button
        on:click={exportCsv}
        class="px-5 py-2.5 rounded-full text-sm font-semibold border transition-all hover:bg-white/50"
        style="border-color: var(--color-outline-variant); color: var(--color-primary); background: rgba(255,255,255,0.4);"
      >
        <span class="material-symbols-outlined align-middle text-base mr-1">download</span>
        次回用CSV出力
      </button>
      <button
        type="button"
        on:click={onOpenStats}
        class="px-5 py-2.5 rounded-full text-sm font-semibold border transition-all hover:bg-white/50"
        style="border-color: var(--color-outline-variant); color: var(--color-on-surface); background: rgba(255,255,255,0.4);"
      >
        <span class="material-symbols-outlined align-middle text-base mr-1">query_stats</span>
        当番統計
      </button>
    {/if}
  </div>

  {#if nextHistoryState}
    <div
      class="glass-panel rounded-xl px-3 py-2.5 flex flex-wrap items-baseline gap-x-6 gap-y-1.5 text-xs"
      style="color: var(--color-on-surface);"
    >
      <span
        ><span class="font-bold uppercase tracking-wider" style="color: var(--color-outline);">CSV</span>
        {nextHistoryState.start_date ?? '-'}〜{nextHistoryState.end_date ?? '-'} / {nextHistoryState.total_entries}件</span
      >
      <span
        ><span class="font-bold uppercase tracking-wider" style="color: var(--color-outline);">直近夜</span>
        {nextHistoryState.latest_night_person_name ?? '-'} {nextHistoryState.latest_night_date ? `（${nextHistoryState.latest_night_date}）` : ''}</span
      >
    </div>
  {/if}

  <!-- エラー / 警告 -->
  {#if $errorMsg}
    <div class="rounded-xl p-4 text-sm font-semibold" style="background: var(--color-error-container); color: var(--color-error);">
      <span class="material-symbols-outlined align-middle text-base mr-1">error</span>
      {$errorMsg}
    </div>
  {/if}
  {#if $warnings && $warnings.length > 0}
    <div class="rounded-xl p-4 space-y-1" style="background: #fff8e1; border: 1px solid #ffe082;">
      <p class="text-xs font-bold uppercase tracking-widest mb-2" style="color: #7c6300;">警告</p>
      {#each $warnings as w}
        <p class="text-sm" style="color: #5a4700;">{w}</p>
      {/each}
    </div>
  {/if}

  {#if startDate && endDate}
    <div
      class="rounded-xl overflow-hidden border"
      style="border-color: {ngListInView.length > 0 ? 'rgba(220, 38, 38, 0.4)' : 'rgba(255,255,255,0.4)'}; background: {ngListInView.length > 0 ? 'rgba(254, 242, 242, 0.75)' : 'rgba(255,255,255,0.2)'};"
    >
      <div
        class="px-3 py-1.5 flex flex-wrap items-center gap-2"
        style="background: {ngListInView.length > 0 ? 'rgba(220, 38, 38, 0.1)' : 'rgba(255,255,255,0.3)'}; border-bottom: 1px solid rgba(0,0,0,0.06);"
      >
        <p class="text-xs font-bold" style="color: var(--color-on-surface);">
          NG {startDate}〜{endDate} <span class="tabular-nums" style="color: var(--color-outline);">（{ngListInView.length}）</span>
        </p>
      </div>
      {#if ngListInView.length > 0}
        <ul class="max-h-28 overflow-y-auto text-[11px] leading-snug" style="color: var(--color-on-surface);">
          {#each ngListInView as ng, i (ng.start_date + '-' + ng.end_date + '-' + (ng.person_name ?? 'all') + '-' + i)}
            <li
              class="px-2 py-1 border-b border-black/[0.06] flex flex-wrap items-baseline gap-x-1.5 gap-y-0"
              style="background: {ng.person_name == null ? 'rgba(251, 191, 36, 0.2)' : 'rgba(255,255,255,0.35)'};"
            >
              <span class="font-mono tabular-nums opacity-80 shrink-0"
                >{ng.start_date}–{ng.end_date}</span
              >
              <span
                class="font-extrabold text-[9px] px-1 rounded"
                style="background: {ng.person_name == null ? '#d97706' : '#e11d48'}; color: white;"
                >{ng.person_name == null ? '全' : '個'}</span
              >
              <span class="font-semibold">{ng.person_name ?? '全員'}</span
              >{#if ng.reason}<span style="color: var(--color-outline);">· {ng.reason}</span>{/if}
            </li>
          {/each}
        </ul>
      {:else}
        <p class="px-3 py-1.5 text-[11px]" style="color: var(--color-outline);">重なるNG登録なし</p>
      {/if}
    </div>
  {/if}

  {#if displayList}
    <div
      class="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg px-2.5 py-1.5 text-[11px] font-semibold"
      style="background: rgba(255,255,255,0.35); border: 1px solid rgba(255,255,255,0.35);"
    >
      <span style="color: var(--color-outline);">凡例</span>
      <span class="inline-flex items-center gap-1" style="color: var(--color-on-surface);">
        <span class="inline-block w-1 h-3 rounded-sm" style="background: #2e7d32;"></span>日
        <span class="inline-block w-1 h-3 rounded-sm" style="background: #1e3a5f;"></span>夜
        <span class="inline-block w-1.5 h-3 rounded-sm" style="background: #e11d48;"></span>NG
      </span>
      <span
        class="inline-flex items-center gap-0.5 ml-auto tabular-nums"
        style="color: {ngConflictCount > 0 ? '#b91c1c' : 'var(--color-outline)'};"
      >
        {ngConflictCount > 0 ? '⚠' : '✓'}NG抵触 {ngConflictCount}枠
      </span>
    </div>
    {#if ngConflictCount > 0}
      <p class="text-[11px] font-semibold px-1" style="color: #991b1b;">赤左線の枠を優先的に入れ替えてください</p>
    {/if}
  {/if}

  <!-- 週行カレンダー（7列）: 一画面で週次の当番を俯瞰 -->
  {#if displayList}
    <div class="glass-panel rounded-xl overflow-hidden shadow-md">
      <p class="px-2 py-1 text-[10px] font-bold" style="color: var(--color-outline); border-bottom: 1px solid rgba(0,0,0,0.06);">
        生成 {startDate} 〜 {endDate}
        <span class="font-normal">（週行・月曜起算7列。薄色＝期間外の週揃え）</span>
      </p>
      <div class="max-h-[min(75vh,920px)] overflow-x-auto overflow-y-auto scroll-smooth p-1.5 sm:p-2">
        <div class="min-w-[640px]">
          <div
            class="grid grid-cols-7 gap-px mb-0.5 text-center text-[10px] font-extrabold tabular-nums"
            style="color: var(--color-outline);"
            aria-hidden="true"
          >
            {#each DAY_LABELS as h}<div class="py-0.5">{h}</div>{/each}
          </div>
          {#each calendarWeeks as week (week[0] + '-' + week[6])}
            <div
              class="grid grid-cols-7 gap-px border-t first:border-t-0"
              style="border-color: rgba(0,0,0,0.08);"
            >
              {#each week as d (d)}
                {@const inSel = inSelectedRange(d)}
                {@const rowSlots = d ? byDate[d] || [] : []}
                {@const rowNgN = inSel ? rowSlots.filter((e) => ngInfo(e.person_name, dateOf(e)).violation).length : 0}
                {@const gDay = d ? isGlobalNgDay(d) : false}
                {@const ngsThisDay = d ? ngListForDate(d, $ngEntries) : []}
                <div
                  class="min-w-0 min-h-[7.5rem] sm:min-h-[8rem] rounded-md border p-0.5 sm:p-1 flex flex-col gap-0.5 relative"
                  style="border-color: {inSel
                    ? rowNgN > 0
                      ? 'rgba(220, 38, 38, 0.45)'
                      : gDay
                        ? 'rgba(245, 158, 11, 0.5)'
                        : 'rgba(0,0,0,0.1)'
                    : 'rgba(0,0,0,0.04)'}; background: {inSel
                    ? rowNgN > 0
                      ? 'rgba(254, 202, 202, 0.22)'
                      : gDay
                        ? 'rgba(254, 243, 199, 0.4)'
                        : d && isWeekend(d)
                          ? 'rgba(255,255,255,0.4)'
                          : 'rgba(255,255,255,0.15)'
                    : 'rgba(0,0,0,0.02)'}; opacity: {inSel ? 1 : 0.55};"
                >
                  {#if d}
                    <div class="flex items-start justify-between gap-0.5 leading-none shrink-0">
                      <span
                        class="text-[10px] sm:text-[11px] font-bold tabular-nums truncate"
                        style="color: {inSel && d && isWeekend(d) ? 'var(--color-primary)' : 'var(--color-on-surface)'};"
                        title={d}
                      >
                        {d.slice(5).replace('-', '/')}
                      </span>
                      <span
                        class="text-[9px] font-bold shrink-0"
                        style="color: var(--color-outline);"
                        >{dayLabel(d)}</span
                      >
                    </div>
                    {#if inSel && ngsThisDay.length > 0}
                      <p
                        class="text-[8px] font-bold leading-tight px-0.5 py-0 rounded truncate w-full"
                        style="color: #991b1b; background: rgba(254, 202, 202, 0.4);"
                        title={ngsThisDay
                          .map(
                            (ng) =>
                              (ng.person_name == null ? '全体' : ng.person_name) + (ng.reason ? ` ${ng.reason}` : '')
                          )
                          .join(' / ')}
                      >
                        NG {ngsThisDay.length}件
                      </p>
                    {/if}
                    {#if inSel && rowNgN > 0}
                      <p class="text-[8px] font-extrabold" style="color: #b91c1c;">抵触 {rowNgN}枠</p>
                    {/if}
                    {#if inSel}
                      <div class="flex-1 flex flex-col gap-0.5 min-h-0 pt-0.5">
                        {#if rowSlots.length > 0}
                          {#each sortedEntries(rowSlots) as entry (slotKey(entry) + d)}
                            {@const ngi = ngInfo(entry.person_name, dateOf(entry))}
                            <div
                              class="relative flex-1 min-h-0 min-w-0 rounded overflow-hidden pl-0.5 pr-0.5 py-0.5 flex items-center"
                              class:ring-1={ngi.violation}
                              class:ring-rose-500={ngi.violation}
                              style="background: {ngi.violation ? 'rgba(254, 226, 226, 0.9)' : 'rgba(255,255,255,0.5)'}; border: 1px solid {ngi.violation
                                ? 'rgba(220, 38, 38, 0.45)'
                                : 'rgba(255,255,255,0.4)'};"
                              title={ngi.violation
                                ? (ngi.global ? '全体不可' : '当番NG') + (ngi.reason ? ` — ${ngi.reason}` : '')
                                : ''}
                            >
                              <div
                                class="absolute left-0 top-0 bottom-0 w-0.5"
                                style="background: {ngi.violation
                                  ? '#e11d48'
                                  : entry.shift_category === 'Night'
                                    ? '#1e3a5f'
                                    : '#2e7d32'}"
                              ></div>
                              <div class="pl-1 w-full min-w-0 flex items-center gap-0.5">
                                <span
                                  class="shrink-0 w-3.5 text-[8px] font-extrabold text-center"
                                  style="color: var(--color-outline);"
                                >
                                  {entry.shift_category === 'Night' ? '夜' : String(entry.shift_index)}</span
                                >
                                <label class="min-w-0 flex-1 block">
                                  <span class="sr-only">担当者</span>
                                  <select
                                    class="w-full min-w-0 max-w-full rounded border text-[9px] sm:text-[10px] font-bold leading-tight py-0.5 pl-0.5 pr-4 truncate focus:outline-none focus:ring-1"
                                    style="border-color: {ngi.violation
                                      ? 'rgba(244, 63, 94, 0.5)'
                                      : 'var(--color-outline-variant)'}; color: var(--color-on-surface); background: rgba(255,255,255,0.9);"
                                    value={entry.person_name}
                                    on:change={(e) => updatePerson(entry, e.currentTarget.value)}
                                  >
                                    {#each candidateNames(entry) as name (name)}
                                      {@const cNg = ngInfo(name, dateOf(entry))}
                                      <option value={name}
                                        >{name}{cNg.violation ? '※NG' : ''}</option
                                      >
                                    {/each}
                                  </select>
                                </label>
                              </div>
                            </div>
                          {/each}
                        {:else}
                          <p class="text-[9px] px-0.5" style="color: var(--color-outline);">割当なし</p>
                        {/if}
                      </div>
                    {:else}
                      <p class="text-[9px] mt-auto" style="color: var(--color-outline);">期間外</p>
                    {/if}
                  {/if}
                </div>
              {/each}
            </div>
          {/each}
        </div>
      </div>
    </div>
  {:else}
    <div class="glass-panel rounded-2xl p-16 text-center" style="color: var(--color-on-surface-variant);">
      <span class="material-symbols-outlined text-5xl mb-4 block" style="color: var(--color-outline-variant);">calendar_month</span>
      <p class="text-sm">期間を選択して「シフト生成」を押してください</p>
    </div>
  {/if}
</div>
