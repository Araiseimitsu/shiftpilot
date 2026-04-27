<script>
  import { onMount } from 'svelte'
  import { api } from './api.js'

  const DAY_LABELS = ['月', '火', '水', '木', '金', '土', '日']

  let historySource = null
  let entries = []
  let historyState = null
  let panelTab = 'summary'
  let loadError = ''

  function groupByDate(rows) {
    const map = {}
    for (const e of rows) {
      const d = String(e.date)
      if (!map[d]) map[d] = []
      map[d].push(e)
    }
    return map
  }

  /** 1日あたり日勤1・2・夜勤の3枠（CSVの列に対応） */
  function buildDayRows(rows) {
    const by = groupByDate(rows)
    return Object.keys(by)
      .sort()
      .map((date) => {
        let day1 = '—'
        let day2 = '—'
        let night = '—'
        for (const e of by[date]) {
          if (e.shift_category === 'Day' && e.shift_index === 1) day1 = e.person_name
          if (e.shift_category === 'Day' && e.shift_index === 2) day2 = e.person_name
          if (e.shift_category === 'Night') night = e.person_name
        }
        return { date, day1, day2, night }
      })
  }

  function dayLabel(dateStr) {
    const d = new Date(dateStr)
    return DAY_LABELS[d.getDay() === 0 ? 6 : d.getDay() - 1]
  }

  function isWeekend(dateStr) {
    const d = new Date(dateStr)
    return d.getDay() === 0 || d.getDay() === 6
  }

  onMount(async () => {
    loadError = ''
    const [src, rows, state] = await Promise.allSettled([
      api.getHistorySource(),
      api.getHistory(),
      api.getHistoryState(),
    ])
    if (src.status === 'fulfilled') historySource = src.value
    if (rows.status === 'fulfilled') entries = rows.value
    if (state.status === 'fulfilled') historyState = state.value
    if (rows.status === 'rejected') {
      loadError = rows.reason?.message ?? String(rows.reason)
    } else if (state.status === 'rejected') {
      loadError = state.reason?.message ?? String(state.reason)
    } else if (src.status === 'rejected') {
      loadError = src.reason?.message ?? String(src.reason)
    }
  })

  $: dayRows = buildDayRows(entries)
</script>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />

<div class="space-y-6">
  {#if loadError}
    <div class="rounded-xl p-4 text-sm font-semibold" style="background: var(--color-error-container); color: var(--color-error);">
      <span class="material-symbols-outlined align-middle text-base mr-1">error</span>
      {loadError}
    </div>
  {/if}

  <div class="glass-panel rounded-2xl overflow-hidden">
    <div
      class="flex gap-0 border-b"
      style="border-color: rgba(0,0,0,0.08);"
      role="tablist"
      aria-label="過去履歴の表示切替"
    >
      <button
        type="button"
        role="tab"
        aria-selected={panelTab === 'summary'}
        class="px-5 py-3 text-sm font-semibold transition-colors"
        class:border-b-2={panelTab === 'summary'}
        style={panelTab === 'summary'
          ? 'color: var(--color-primary); border-color: var(--color-primary); background: rgba(255,255,255,0.35);'
          : 'color: var(--color-on-surface-variant); border-color: transparent;'}
        on:click={() => (panelTab = 'summary')}
      >
        概要
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={panelTab === 'content'}
        class="px-5 py-3 text-sm font-semibold transition-colors"
        class:border-b-2={panelTab === 'content'}
        style={panelTab === 'content'
          ? 'color: var(--color-primary); border-color: var(--color-primary); background: rgba(255,255,255,0.35);'
          : 'color: var(--color-on-surface-variant); border-color: transparent;'}
        on:click={() => (panelTab = 'content')}
      >
        日別（1日2〜3枠）
      </button>
    </div>

    {#if panelTab === 'summary'}
      <div class="p-5 space-y-5">
        {#if historySource}
          <div class="flex flex-col gap-1">
            <p class="text-xs font-bold uppercase tracking-widest" style="color: var(--color-outline);">読み込み中の履歴 CSV</p>
            <p class="text-sm font-semibold leading-relaxed" style="color: var(--color-on-surface);">
              {#if historySource.kind === 'default'}
                リポジトリ同梱: <code class="text-xs font-mono px-1.5 py-0.5 rounded" style="background: rgba(0,0,0,0.06);">{historySource.label}</code>
              {:else if historySource.kind === 'upload'}
                アップロード: <code class="text-xs font-mono px-1.5 py-0.5 rounded" style="background: rgba(0,0,0,0.06);">{historySource.label}</code>
              {:else}
                {historySource.label}
              {/if}
              <span class="ml-2 text-xs font-medium" style="color: var(--color-outline);">（{historySource.row_count} 件）</span>
            </p>
            <p class="text-[11px] leading-snug" style="color: var(--color-outline);">
              デフォルト想定パス: <code class="font-mono">{historySource.default_path}</code>
            </p>
          </div>
        {/if}

        {#if historyState}
          <div class="grid gap-4 md:grid-cols-5">
            <div>
              <p class="text-xs font-bold uppercase tracking-widest" style="color: var(--color-outline);">参照履歴期間</p>
              <p class="mt-1 text-sm font-semibold" style="color: var(--color-on-surface);">
                {historyState.start_date ?? '-'} 〜 {historyState.end_date ?? '-'}
              </p>
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-widest" style="color: var(--color-outline);">履歴件数</p>
              <p class="mt-1 text-sm font-semibold" style="color: var(--color-on-surface);">{historyState.total_entries} 件</p>
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-widest" style="color: var(--color-outline);">対象者</p>
              <p class="mt-1 text-sm font-semibold" style="color: var(--color-on-surface);">{historyState.people?.length ?? 0} 名</p>
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-widest" style="color: var(--color-outline);">次回計算</p>
              <p class="mt-1 text-sm font-semibold" style="color: var(--color-on-surface);">履歴反映済み</p>
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-widest" style="color: var(--color-outline);">直近夜勤</p>
              <p class="mt-1 text-sm font-semibold" style="color: var(--color-on-surface);">
                {historyState.latest_night_person_name ?? '-'} / {historyState.latest_night_date ?? '-'}
              </p>
            </div>
          </div>
        {/if}
      </div>
    {:else}
      <div class="p-0">
        <div class="px-4 py-2 text-xs font-medium" style="color: var(--color-outline);">
          1日1行 · 日勤1番・日勤2番・夜勤 · 計 {dayRows.length} 日分
        </div>
        <div class="max-h-[min(70vh,640px)] overflow-auto border-t" style="border-color: rgba(0,0,0,0.06);">
          {#if dayRows.length === 0}
            <div class="p-8 text-center text-sm" style="color: var(--color-on-surface-variant);">
              表示する日がありません。{historySource?.default_path
                ? ` ${historySource.default_path} を配置するか、履歴をアップロードしてください。`
                : ''}
            </div>
          {:else}
            <table class="w-full text-left text-sm border-collapse">
              <thead
                class="sticky top-0 z-10 text-xs font-bold uppercase tracking-widest"
                style="color: var(--color-outline); background: rgba(255,255,255,0.92); backdrop-filter: blur(8px); box-shadow: 0 1px 0 rgba(0,0,0,0.06);"
              >
                <tr>
                  <th class="px-3 py-2.5 font-semibold w-[7.5rem]">日付</th>
                  <th class="px-2 py-2.5 w-10">曜</th>
                  <th class="px-2 py-2.5 min-w-[6rem]">1番手（日勤）</th>
                  <th class="px-2 py-2.5 min-w-[6rem]">2番手（日勤）</th>
                  <th class="px-3 py-2.5 min-w-[6rem]">夜勤</th>
                </tr>
              </thead>
              <tbody>
                {#each dayRows as row (row.date)}
                  <tr
                    class="border-t transition-colors"
                    style="border-color: rgba(0,0,0,0.05); background: {isWeekend(row.date) ? 'rgba(255,255,255,0.35)' : 'transparent'};"
                  >
                    <td class="px-3 py-2.5 font-mono text-[13px] align-top" style="color: var(--color-on-surface);">{row.date}</td>
                    <td class="px-2 py-2.5 align-top" style="color: var(--color-outline);">{dayLabel(row.date)}</td>
                    <td class="px-2 py-2.5 font-medium align-top" style="color: #1b5e20;">{row.day1}</td>
                    <td class="px-2 py-2.5 font-medium align-top" style="color: #2e7d32;">{row.day2}</td>
                    <td class="px-3 py-2.5 font-medium align-top" style="color: #1e3a5f;">{row.night}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>
