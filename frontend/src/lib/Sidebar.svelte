<script>
  export let activePage = 'schedule'
  export let onNavigate = () => {}
</script>

<aside class="fixed left-0 top-0 h-screen w-64 glass-panel flex flex-col py-8 px-5 z-50" style="border-right: 1px solid rgba(255,255,255,0.3);">
  <div class="flex items-center gap-3 mb-10 px-2">
    <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: var(--color-primary-container);">
      <span class="material-symbols-outlined text-white" style="font-variation-settings:'FILL' 1;">rocket_launch</span>
    </div>
    <div>
      <h1 class="text-xl font-bold tracking-tight" style="color: #2C4A52;">ShiftPilot</h1>
      <p class="text-[10px] uppercase tracking-widest font-bold" style="color: var(--color-outline);">Management Console</p>
    </div>
  </div>

  <nav class="flex-1 flex flex-col gap-1">
    {#each [
      { id: 'schedule', icon: 'calendar_month', label: 'スケジュール' },
      { id: 'stats', icon: 'query_stats', label: '当番統計' },
      { id: 'history', icon: 'history', label: '過去の履歴' },
      { id: 'staff', icon: 'group', label: 'スタッフ / NG' },
    ] as item}
      <button
        class="flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200"
        class:active-nav={activePage === item.id}
        style={activePage === item.id
          ? 'background:rgba(255,255,255,0.4); color: var(--color-primary); font-weight:600;'
          : 'color: var(--color-on-surface-variant);'}
        on:click={() => onNavigate(item.id)}
      >
        <span class="material-symbols-outlined" style={activePage === item.id ? "font-variation-settings:'FILL' 1;" : ''}>
          {item.icon}
        </span>
        <span>{item.label}</span>
      </button>
    {/each}
  </nav>
</aside>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
