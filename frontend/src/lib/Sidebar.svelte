<script>
  export let activePage = 'schedule'
  export let onNavigate = () => {}
  export let collapsed = false
</script>

<aside
  class="fixed left-0 top-0 h-screen glass-panel flex flex-col py-8 z-50 transition-all duration-300"
  class:w-16={collapsed}
  class:w-64={!collapsed}
  class:px-2={collapsed}
  class:px-5={!collapsed}
  style="border-right: 1px solid rgba(255,255,255,0.3);"
>
  <div class="flex items-center mb-10" class:justify-center={collapsed} class:gap-3={!collapsed} class:px-2={!collapsed}>
    <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style="background: var(--color-primary-container);">
      <span class="material-symbols-outlined text-white" style="font-variation-settings:'FILL' 1;">rocket_launch</span>
    </div>
    {#if !collapsed}
      <div class="overflow-hidden whitespace-nowrap">
        <h1 class="text-xl font-bold tracking-tight" style="color: #2C4A52;">ShiftPilot</h1>
        <p class="text-[10px] uppercase tracking-widest font-bold" style="color: var(--color-outline);">Management Console</p>
      </div>
    {/if}
  </div>

  <nav class="flex-1 flex flex-col gap-1">
    {#each [
      { id: 'schedule', icon: 'calendar_month', label: 'スケジュール' },
      { id: 'stats', icon: 'query_stats', label: '当番統計' },
      { id: 'history', icon: 'history', label: '過去の履歴' },
      { id: 'staff', icon: 'group', label: 'スタッフ / NG' },
    ] as item}
      <button
        class="flex items-center rounded-xl text-left transition-all duration-200 py-3"
        class:px-2={collapsed}
        class:px-4={!collapsed}
        class:gap-3={!collapsed}
        class:justify-center={collapsed}
        class:active-nav={activePage === item.id}
        style={activePage === item.id
          ? 'background:rgba(255,255,255,0.4); color: var(--color-primary); font-weight:600;'
          : 'color: var(--color-on-surface-variant);'}
        on:click={() => onNavigate(item.id)}
        title={collapsed ? item.label : ''}
      >
        <span class="material-symbols-outlined shrink-0" style={activePage === item.id ? "font-variation-settings:'FILL' 1;" : ''}>
          {item.icon}
        </span>
        {#if !collapsed}
          <span class="whitespace-nowrap">{item.label}</span>
        {/if}
      </button>
    {/each}
  </nav>

  <button
    class="mt-auto mx-auto flex items-center justify-center w-8 h-8 rounded-full transition-all hover:bg-white/30"
    style="color: var(--color-outline);"
    on:click={() => collapsed = !collapsed}
    aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
  >
    <span class="material-symbols-outlined">{collapsed ? 'chevron_right' : 'chevron_left'}</span>
  </button>
</aside>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
