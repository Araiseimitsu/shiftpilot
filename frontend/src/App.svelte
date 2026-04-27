<script>
  import Sidebar from './lib/Sidebar.svelte'
  import ShiftCalendar from './lib/ShiftCalendar.svelte'
  import ScheduleStats from './lib/ScheduleStats.svelte'
  import PastHistory from './lib/PastHistory.svelte'
  import StaffManager from './lib/StaffManager.svelte'

  let activePage = 'schedule'

  const PAGE_TITLES = {
    schedule: 'シフトスケジュール',
    stats: '当番統計',
    history: '過去の履歴',
    staff: 'スタッフ / NGエントリ管理',
  }
</script>

<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
/>

<Sidebar {activePage} onNavigate={(p) => activePage = p} />

<!-- ヘッダー -->
<header
  class="fixed top-0 right-0 h-16 flex items-center px-10 z-40"
  style="left: 256px; background: rgba(255,255,255,0.4); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.3);"
>
  <h2 class="text-lg font-semibold" style="color: var(--color-primary); letter-spacing: -0.01em;">
    {PAGE_TITLES[activePage]}
  </h2>
</header>

<!-- メインコンテンツ -->
<main style="margin-left: 256px; padding-top: 64px; padding: 80px 32px 32px; min-height: 100vh;">
  <div style="max-width: min(100%, 88rem); margin: 0 auto;">
    {#if activePage === 'schedule'}
      <ShiftCalendar onOpenStats={() => (activePage = 'stats')} />
    {:else if activePage === 'stats'}
      <ScheduleStats onOpenSchedule={() => (activePage = 'schedule')} />
    {:else if activePage === 'history'}
      <PastHistory />
    {:else if activePage === 'staff'}
      <StaffManager />
    {/if}
  </div>
</main>
