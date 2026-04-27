<script>
  import { members, scheduleView } from './store.js'
  import { computeScheduleStats } from './scheduleStats.js'

  export let onOpenSchedule = () => {}

  let sortKey = 'totalSlots'
  let sortDir = -1

  function gapLabel(v) {
    if (v == null) return '—'
    return `${v}日`
  }

  function toggleSort(key) {
    if (sortKey === key) sortDir = -sortDir
    else {
      sortKey = key
      sortDir = key === 'name' ? 1 : -1
    }
  }

  $: stats = (() => {
    const v = $scheduleView
    if (!v?.entries?.length) return null
    return computeScheduleStats(v.entries)
  })()

  $: rangeLabel = (() => {
    const v = $scheduleView
    if (v?.rangeStart && v?.rangeEnd) return `${v.rangeStart} 〜 ${v.rangeEnd}`
    return stats?.range?.start && stats?.range?.end
      ? `${stats.range.start} 〜 ${stats.range.end}`
      : ''
  })()

  $: unassigned = (() => {
    if (!stats) return []
    const active = $members.filter((m) => m.active).map((m) => m.name)
    return active.filter((n) => !stats.assignedNames.has(n)).sort((a, b) => a.localeCompare(b, 'ja'))
  })()

  $: sortedPeople = (() => {
    if (!stats?.people) return []
    const mult = sortDir
    const key = sortKey
    return [...stats.people].sort((a, b) => {
      if (key === 'name') return mult * a.name.localeCompare(b.name, 'ja')
      const av = a[key]
      const bv = b[key]
      if (av == null && bv == null) return mult * a.name.localeCompare(b.name, 'ja')
      if (av == null) return 1
      if (bv == null) return -1
      if (av !== bv) return mult * (av < bv ? -1 : av > bv ? 1 : 0)
      return a.name.localeCompare(b.name, 'ja')
    })
  })()
</script>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />

<div class="space-y-4">
  <div class="flex flex-wrap items-center gap-2">
    <button
      type="button"
      on:click={onOpenSchedule}
      class="inline-flex items-center gap-1 px-4 py-2 rounded-full text-sm font-semibold border transition-all hover:bg-white/50"
      style="border-color: var(--color-outline-variant); color: var(--color-primary); background: rgba(255,255,255,0.45);"
    >
      <span class="material-symbols-outlined text-base">arrow_back</span>
      スケジュールに戻る
    </button>
  </div>

  {#if !stats}
    <div class="glass-panel rounded-2xl p-14 text-center" style="color: var(--color-on-surface-variant);">
      <span class="material-symbols-outlined text-5xl mb-4 block" style="color: var(--color-outline-variant);">query_stats</span>
      <p class="text-sm font-semibold mb-1" style="color: var(--color-on-surface);">まだ統計を表示できません</p>
      <p class="text-xs max-w-md mx-auto" style="color: var(--color-outline);">
        「スケジュール」で期間を選びシフト生成すると、ここに担当回数・当番の間隔などが表示されます。カレンダー上の入れ替えも反映されます。
      </p>
    </div>
  {:else}
    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div class="glass-panel rounded-xl p-4">
        <p class="text-[10px] font-bold uppercase tracking-widest mb-1" style="color: var(--color-outline);">対象期間</p>
        <p class="text-sm font-bold tabular-nums" style="color: var(--color-on-surface);">{rangeLabel}</p>
      </div>
      <div class="glass-panel rounded-xl p-4">
        <p class="text-[10px] font-bold uppercase tracking-widest mb-1" style="color: var(--color-outline);">割当スロット合計</p>
        <p class="text-2xl font-bold tabular-nums" style="color: var(--color-primary);">{stats.totalSlots}</p>
      </div>
      <div class="glass-panel rounded-xl p-4">
        <p class="text-[10px] font-bold uppercase tracking-widest mb-1" style="color: var(--color-outline);">担当者（名）</p>
        <p class="text-2xl font-bold tabular-nums" style="color: var(--color-on-surface);">{stats.assignedCount}</p>
      </div>
      <div class="glass-panel rounded-xl p-4">
        <p class="text-[10px] font-bold uppercase tracking-widest mb-1" style="color: var(--color-outline);">凡例</p>
        <p class="text-[11px] leading-snug" style="color: var(--color-on-surface-variant);">
          <span class="font-semibold" style="color: var(--color-on-surface);">イベント間隔</span>：夜勤は週を1回と数え、日勤は各日。最も詰まっている箇所の日数です。
        </p>
      </div>
    </div>

    {#if unassigned.length > 0}
      <div
        class="rounded-xl px-3 py-2.5 text-xs"
        style="background: rgba(254, 243, 199, 0.5); border: 1px solid rgba(245, 158, 11, 0.35); color: #713f12;"
      >
        <span class="font-bold">この期間で一度も割り当てがないアクティブメンバー（{unassigned.length}）</span>
        <span class="opacity-90"> — {unassigned.join('、')}</span>
      </div>
    {/if}

    <div class="glass-panel rounded-xl overflow-hidden shadow-md">
      <div class="px-3 py-2 border-b flex flex-wrap items-center gap-2" style="border-color: rgba(0,0,0,0.06);">
        <span class="material-symbols-outlined text-lg" style="color: var(--color-outline);">table</span>
        <h3 class="text-sm font-bold" style="color: var(--color-on-surface);">担当別サマリ</h3>
        <span class="text-[10px] ml-auto" style="color: var(--color-outline);">列見出しでソート</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs sm:text-sm" style="color: var(--color-on-surface);">
          <thead>
            <tr style="background: rgba(255,255,255,0.35); color: var(--color-outline);">
              <th class="p-2.5 font-bold whitespace-nowrap">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('name')}>
                  名前 {sortKey === 'name' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
              <th class="p-2.5 font-bold tabular-nums text-right whitespace-nowrap">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('totalSlots')}>
                  合計枠 {sortKey === 'totalSlots' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
              <th class="p-2.5 font-bold tabular-nums text-right whitespace-nowrap hidden sm:table-cell">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('day1')}>
                  日1 {sortKey === 'day1' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
              <th class="p-2.5 font-bold tabular-nums text-right whitespace-nowrap hidden sm:table-cell">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('day2')}>
                  日2 {sortKey === 'day2' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
              <th class="p-2.5 font-bold tabular-nums text-right whitespace-nowrap">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('nightDays')}>
                  夜(日) {sortKey === 'nightDays' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
              <th class="p-2.5 font-bold tabular-nums text-right whitespace-nowrap hidden md:table-cell">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('nightWeeks')}>
                  夜(週) {sortKey === 'nightWeeks' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
              <th class="p-2.5 font-bold tabular-nums text-right whitespace-nowrap">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('minDayOnlyGapDays')}>
                  日勤最短 {sortKey === 'minDayOnlyGapDays' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
              <th class="p-2.5 font-bold tabular-nums text-right whitespace-nowrap">
                <button type="button" class="font-bold hover:underline" on:click={() => toggleSort('minMergedGapDays')}>
                  イベント最短 {sortKey === 'minMergedGapDays' ? (sortDir > 0 ? '↑' : '↓') : ''}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {#each sortedPeople as p (p.name)}
              <tr class="border-t" style="border-color: rgba(0,0,0,0.06); background: rgba(255,255,255,0.12);">
                <td class="p-2.5 font-semibold whitespace-nowrap">{p.name}</td>
                <td class="p-2.5 tabular-nums text-right font-bold">{p.totalSlots}</td>
                <td class="p-2.5 tabular-nums text-right hidden sm:table-cell">{p.day1}</td>
                <td class="p-2.5 tabular-nums text-right hidden sm:table-cell">{p.day2}</td>
                <td class="p-2.5 tabular-nums text-right">{p.nightDays}</td>
                <td class="p-2.5 tabular-nums text-right hidden md:table-cell">{p.nightWeeks}</td>
                <td class="p-2.5 tabular-nums text-right" title="日勤のみ、日付どうしの最短間隔">{gapLabel(p.minDayOnlyGapDays)}</td>
                <td class="p-2.5 tabular-nums text-right" title="夜勤は週あたり1イベントとして集約">{gapLabel(p.minMergedGapDays)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <p class="text-[11px] px-1 leading-relaxed" style="color: var(--color-outline);">
      「日勤最短」は土日枠だけを対象に、連続する日勤日の間の最小日数です。「イベント最短」は夜勤を週単位にまとめたうえで、日勤各日＋夜勤週の開始日を並べたときの最小間隔です（同じ週に日勤と夜勤がある場合は別イベントとして近くなります）。
    </p>
  {/if}
</div>
