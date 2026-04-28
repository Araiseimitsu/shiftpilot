<script>
  import { onMount } from 'svelte'
  import { members, ngEntries, errorMsg, manualMembers } from './store.js'
  import { api } from './api.js'
  import NgPasteBulk from './NgPasteBulk.svelte'

  let activeTab = 'auto' // 'auto' | 'manual'

  let newNg = { person_name: '', start_date: '', end_date: '', reason: '' }
  let showForm = false

  let newMemberName = ''
  let newMemberFlags = { assignable_day1: true, assignable_day2: true, assignable_night: true }
  let showAddMember = false

  onMount(async () => {
    try {
      const [m, ng] = await Promise.all([api.getMembers(), api.getNgEntries()])
      members.set(m)
      ngEntries.set(ng)
    } catch (e) {
      errorMsg.set(e.message)
    }
  })

  async function toggleFlag(member, flag) {
    const flags = {
      assignable_day1: member.assignable_day1,
      assignable_day2: member.assignable_day2,
      assignable_night: member.assignable_night,
      [flag]: !member[flag],
    }
    try {
      const result = await api.updateMemberFlags(member.name, flags)
      members.update(list => list.map(m => m.name === member.name ? result : m))
    } catch (e) {
      errorMsg.set(e.message)
    }
  }

  async function addMember() {
    if (!newMemberName.trim()) return
    try {
      const created = await api.createMember({
        name: newMemberName.trim(),
        assignable_day1: newMemberFlags.assignable_day1,
        assignable_day2: newMemberFlags.assignable_day2,
        assignable_night: newMemberFlags.assignable_night,
      })
      members.update(list => [...list, created])
      newMemberName = ''
      newMemberFlags = { assignable_day1: true, assignable_day2: true, assignable_night: true }
      showAddMember = false
    } catch (e) {
      errorMsg.set(e.message)
    }
  }

  async function removeMember(name) {
    if (!confirm(`${name} を削除しますか？`)) return
    try {
      await api.deleteMember(name)
      members.update(list => list.filter(m => m.name !== name))
    } catch (e) {
      errorMsg.set(e.message)
    }
  }

  // --- 手入力用スタッフ管理（ローカル） ---
  let newManualName = ''
  let showAddManual = false

  function addManualMember() {
    if (!newManualName.trim()) return
    const name = newManualName.trim()
    if ($manualMembers.some(m => m.name === name)) {
      errorMsg.set(`${name} は既に存在します`)
      return
    }
    manualMembers.update(list => [...list, { name }])
    newManualName = ''
    showAddManual = false
    errorMsg.set('')
  }

  function removeManualMember(name) {
    if (!confirm(`${name} を削除しますか？`)) return
    manualMembers.update(list => list.filter(m => m.name !== name))
  }

  async function addNg() {
    try {
      const created = await api.createNgEntry({
        ...newNg,
        person_name: newNg.person_name || null,
      })
      ngEntries.update(list => [...list, created])
      newNg = { person_name: '', start_date: '', end_date: '', reason: '' }
      showForm = false
    } catch (e) {
      errorMsg.set(e.message)
    }
  }

  async function removeNg(index) {
    try {
      await api.deleteNgEntry(index)
      ngEntries.update(list => list.filter((_, i) => i !== index))
    } catch (e) {
      errorMsg.set(e.message)
    }
  }
</script>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />

<div class="space-y-6">
  <!-- タブ -->
  <div class="flex gap-2">
    <button
      on:click={() => activeTab = 'auto'}
      class="px-4 py-2 rounded-xl text-sm font-semibold transition-all"
      style={activeTab === 'auto'
        ? 'background: var(--color-primary); color: var(--color-on-primary);'
        : 'background: rgba(255,255,255,0.3); color: var(--color-on-surface);'}
    >
      自動生成用スタッフ
    </button>
    <button
      on:click={() => activeTab = 'manual'}
      class="px-4 py-2 rounded-xl text-sm font-semibold transition-all"
      style={activeTab === 'manual'
        ? 'background: var(--color-primary); color: var(--color-on-primary);'
        : 'background: rgba(255,255,255,0.3); color: var(--color-on-surface);'}
    >
      手入力用（担当者の設定）
    </button>
  </div>

  <!-- 自動生成用スタッフ -->
  {#if activeTab === 'auto'}
  <div class="glass-panel rounded-2xl overflow-hidden">
    <div class="px-6 py-4 border-b flex items-center justify-between" style="border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.2);">
      <h2 class="text-sm font-bold uppercase tracking-widest" style="color: var(--color-outline);">スタッフ別割当設定</h2>
      <div class="flex items-center gap-3">
        <span class="text-xs" style="color: var(--color-outline);">{$members.length} 名</span>
        <button
          on:click={() => showAddMember = !showAddMember}
          class="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold text-white transition-all hover:opacity-90"
          style="background: var(--color-primary-container);"
        >
          <span class="material-symbols-outlined text-base">add</span>
          追加
        </button>
      </div>
    </div>

    {#if showAddMember}
      <div class="px-6 py-4 border-b space-y-3" style="border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.15);">
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label for="member-name" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">氏名</label>
            <input
              id="member-name"
              type="text"
              bind:value={newMemberName}
              placeholder="例: 山田"
              class="px-3 py-2 rounded-lg text-sm border focus:outline-none"
              style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
            />
          </div>
          <div class="flex items-end gap-4 pb-1">
            <label class="flex items-center gap-2 text-sm" style="color: var(--color-on-surface);">
              <input type="checkbox" bind:checked={newMemberFlags.assignable_day1} class="rounded" />
              日勤１番
            </label>
            <label class="flex items-center gap-2 text-sm" style="color: var(--color-on-surface);">
              <input type="checkbox" bind:checked={newMemberFlags.assignable_day2} class="rounded" />
              日勤２番
            </label>
            <label class="flex items-center gap-2 text-sm" style="color: var(--color-on-surface);">
              <input type="checkbox" bind:checked={newMemberFlags.assignable_night} class="rounded" />
              夜勤
            </label>
          </div>
        </div>
        <div class="flex gap-2 justify-end">
          <button
            on:click={() => showAddMember = false}
            class="px-4 py-2 rounded-lg text-sm font-semibold border transition-all hover:bg-white/30"
            style="border-color: var(--color-outline-variant); color: var(--color-on-surface-variant);"
          >
            キャンセル
          </button>
          <button
            on:click={addMember}
            disabled={!newMemberName.trim()}
            class="px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
            style="background: var(--color-primary);"
          >
            保存
          </button>
        </div>
      </div>
    {/if}

    <table class="w-full text-left">
      <thead>
        <tr style="background: rgba(255,255,255,0.15); border-bottom: 1px solid rgba(255,255,255,0.2);">
          <th class="px-6 py-3 text-[11px] font-bold uppercase tracking-widest" style="color: var(--color-outline);">氏名</th>
          <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-widest text-center" style="color: var(--color-outline);">日勤１番</th>
          <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-widest text-center" style="color: var(--color-outline);">日勤２番</th>
          <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-widest text-center" style="color: var(--color-outline);">夜勤</th>
          <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-widest text-center" style="color: var(--color-outline);"></th>
        </tr>
      </thead>
      <tbody>
        {#each $members as member}
          <tr class="hover:bg-white/30 transition-colors" style="border-bottom: 1px solid rgba(255,255,255,0.1);">
            <td class="px-6 py-3 flex items-center gap-3">
              <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0" style="background: var(--color-primary-container);">
                {member.name.slice(0, 1)}
              </div>
              <span class="text-sm font-medium" style="color: var(--color-on-surface);">{member.name}</span>
            </td>
            {#each [
              { flag: 'assignable_day1', value: member.assignable_day1 },
              { flag: 'assignable_day2', value: member.assignable_day2 },
              { flag: 'assignable_night', value: member.assignable_night },
            ] as { flag, value }}
              <td class="px-4 py-3 text-center">
                <button
                  on:click={() => toggleFlag(member, flag)}
                  class="inline-flex items-center justify-center w-10 h-6 rounded-full transition-all duration-200 relative"
                  style="background: {value ? 'var(--color-primary-container)' : 'var(--color-surface-container-high)'};"
                  aria-label="{flag} トグル"
                >
                  <span
                    class="absolute w-4 h-4 rounded-full bg-white shadow transition-all duration-200"
                    style="left: {value ? '22px' : '2px'};"
                  ></span>
                </button>
              </td>
            {/each}
            <td class="px-4 py-3 text-center">
              <button
                on:click={() => removeMember(member.name)}
                class="p-1.5 rounded-full transition-colors hover:bg-red-50"
                style="color: var(--color-outline);"
                aria-label="削除"
              >
                <span class="material-symbols-outlined text-base">delete</span>
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  {/if}

  <!-- 手入力用: 担当者名の設定のみ（NG・一括登録は自動生成用タブ） -->
  {#if activeTab === 'manual'}
  <div class="glass-panel rounded-2xl overflow-hidden">
    <div class="px-6 py-4 border-b flex items-center justify-between" style="border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.2);">
      <h2 class="text-sm font-bold uppercase tracking-widest" style="color: var(--color-outline);">手入力用・担当者</h2>
      <div class="flex items-center gap-3">
        <span class="text-xs" style="color: var(--color-outline);">{$manualMembers.length} 名</span>
        <button
          on:click={() => showAddManual = !showAddManual}
          class="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold text-white transition-all hover:opacity-90"
          style="background: var(--color-primary-container);"
        >
          <span class="material-symbols-outlined text-base">add</span>
          追加
        </button>
      </div>
    </div>

    {#if showAddManual}
      <div class="px-6 py-4 border-b space-y-3" style="border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.15);">
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label for="manual-name" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">氏名</label>
            <input
              id="manual-name"
              type="text"
              bind:value={newManualName}
              placeholder="例: 山田"
              class="px-3 py-2 rounded-lg text-sm border focus:outline-none"
              style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
            />
          </div>
        </div>
        <div class="flex gap-2 justify-end">
          <button
            on:click={() => showAddManual = false}
            class="px-4 py-2 rounded-lg text-sm font-semibold border transition-all hover:bg-white/30"
            style="border-color: var(--color-outline-variant); color: var(--color-on-surface-variant);"
          >
            キャンセル
          </button>
          <button
            on:click={addManualMember}
            disabled={!newManualName.trim()}
            class="px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
            style="background: var(--color-primary);"
          >
            保存
          </button>
        </div>
      </div>
    {/if}

    <table class="w-full text-left">
      <thead>
        <tr style="background: rgba(255,255,255,0.15); border-bottom: 1px solid rgba(255,255,255,0.2);">
          <th class="px-6 py-3 text-[11px] font-bold uppercase tracking-widest" style="color: var(--color-outline);">氏名</th>
          <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-widest text-center" style="color: var(--color-outline);"></th>
        </tr>
      </thead>
      <tbody>
        {#each $manualMembers as member}
          <tr class="hover:bg-white/30 transition-colors" style="border-bottom: 1px solid rgba(255,255,255,0.1);">
            <td class="px-6 py-3 flex items-center gap-3">
              <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0" style="background: #7c4dff;">
                {member.name.slice(0, 1)}
              </div>
              <span class="text-sm font-medium" style="color: var(--color-on-surface);">{member.name}</span>
            </td>
            <td class="px-4 py-3 text-center">
              <button
                on:click={() => removeManualMember(member.name)}
                class="p-1.5 rounded-full transition-colors hover:bg-red-50"
                style="color: var(--color-outline);"
                aria-label="削除"
              >
                <span class="material-symbols-outlined text-base">delete</span>
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  {/if}

  {#if activeTab === 'auto'}
  <!-- 一括貼り付け登録 -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <NgPasteBulk shiftType="day" members={$members} />
    <NgPasteBulk shiftType="night" members={$members} />
  </div>

  <!-- NGエントリ管理 -->
  <div class="glass-panel rounded-2xl overflow-hidden">
    <div class="px-6 py-4 border-b flex items-center justify-between" style="border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.2);">
      <h2 class="text-sm font-bold uppercase tracking-widest" style="color: var(--color-outline);">NGエントリ（不可日程）</h2>
      <button
        on:click={() => showForm = !showForm}
        class="flex items-center gap-1 px-4 py-1.5 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90"
        style="background: var(--color-primary-container);"
      >
        <span class="material-symbols-outlined text-base">add</span>
        追加
      </button>
    </div>

    {#if showForm}
      <div class="px-6 py-4 border-b space-y-3" style="border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.15);">
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label for="ng-person" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">担当者（空欄=全体NG）</label>
            <select
              id="ng-person"
              bind:value={newNg.person_name}
              class="px-3 py-2 rounded-lg text-sm border focus:outline-none"
              style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
            >
              <option value="">全体NG</option>
              {#each $members as m}
                <option value={m.name}>{m.name}</option>
              {/each}
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <label for="ng-reason" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">理由</label>
            <input
              id="ng-reason"
              type="text"
              bind:value={newNg.reason}
              placeholder="例: 出張"
              class="px-3 py-2 rounded-lg text-sm border focus:outline-none"
              style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label for="ng-start" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">開始日</label>
            <input
              id="ng-start"
              type="date"
              bind:value={newNg.start_date}
              class="px-3 py-2 rounded-lg text-sm border focus:outline-none"
              style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label for="ng-end" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">終了日</label>
            <input
              id="ng-end"
              type="date"
              bind:value={newNg.end_date}
              class="px-3 py-2 rounded-lg text-sm border focus:outline-none"
              style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
            />
          </div>
        </div>
        <div class="flex gap-2 justify-end">
          <button
            on:click={() => showForm = false}
            class="px-4 py-2 rounded-lg text-sm font-semibold border transition-all hover:bg-white/30"
            style="border-color: var(--color-outline-variant); color: var(--color-on-surface-variant);"
          >
            キャンセル
          </button>
          <button
            on:click={addNg}
            disabled={!newNg.start_date || !newNg.end_date}
            class="px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
            style="background: var(--color-primary);"
          >
            保存
          </button>
        </div>
      </div>
    {/if}

    {#if $ngEntries.length === 0}
      <div class="px-6 py-8 text-center text-sm" style="color: var(--color-outline);">
        NGエントリはありません
      </div>
    {:else}
      <div class="divide-y" style="border-color: rgba(255,255,255,0.1);">
        {#each $ngEntries as ng, i}
          <div class="px-6 py-3 flex items-center gap-3 hover:bg-white/30 transition-colors">
            <span class="material-symbols-outlined text-sm" style="color: var(--color-error);">block</span>
            <div class="flex-1">
              <p class="text-sm font-semibold" style="color: var(--color-on-surface);">
                {ng.person_name ?? '全体'}
                <span class="font-normal ml-2 text-xs" style="color: var(--color-outline);">
                  {ng.start_date} 〜 {ng.end_date}
                </span>
              </p>
              {#if ng.reason}
                <p class="text-xs" style="color: var(--color-on-surface-variant);">{ng.reason}</p>
              {/if}
            </div>
            <button
              on:click={() => removeNg(i)}
              class="p-1.5 rounded-full transition-colors hover:bg-red-50"
              style="color: var(--color-outline);"
            >
              <span class="material-symbols-outlined text-base">delete</span>
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>
  {/if}
</div>
