<script>
  import { ngEntries, errorMsg } from './store.js'
  import { api } from './api.js'
  import { findBestMatch } from './fuzzyMatch.js'

  export let shiftType = 'day' // 'day' | 'night'
  export let members = [] // 既存メンバー名リスト（未登録チェック用）

  let text = ''
  let year = new Date().getFullYear()
  let previewItems = []
  let showPreview = false
  let loading = false
  let manualOverrides = {} // key: originalName, value: resolvedName

  $: panelTitle = shiftType === 'night' ? '夜勤NG 一括貼り付け' : '日勤NG 一括貼り付け'
  $: placeholder = '例：\n山田太郎\n5/10、5/17\n佐藤花子\n5/3,6/6'
  $: memberNames = members.map(m => m.name)

  // 各プレビューアイテムの解決結果
  $: resolvedItems = previewItems.map(item => {
    const original = item.person_name
    if (manualOverrides[original]) {
      return { ...item, resolvedName: manualOverrides[original], method: 'manual' }
    }
    const match = findBestMatch(original, memberNames)
    return { ...item, resolvedName: match.name, method: match.method, score: match.score }
  })

  $: unresolvedItems = resolvedItems.filter(i => !i.resolvedName)

  async function parsePreview() {
    if (!text.trim()) {
      previewItems = []
      showPreview = false
      return
    }
    try {
      loading = true
      manualOverrides = {}
      const res = await api.parseNgBulk(text, year, shiftType)
      previewItems = res.items || []
      showPreview = true
    } catch (e) {
      errorMsg.set(e.message)
    } finally {
      loading = false
    }
  }

  async function register() {
    if (resolvedItems.length === 0) return
    if (unresolvedItems.length > 0) {
      alert(`未解決の名前が ${unresolvedItems.length} 件あります。名前を選択してください。`)
      return
    }
    try {
      loading = true
      // resolvedName で置き換えて登録
      const toRegister = resolvedItems.map(i => ({
        person_name: i.resolvedName,
        dates: i.dates,
      }))
      const res = await api.registerNgBulk(toRegister, shiftType)
      const updated = await api.getNgEntries()
      ngEntries.set(updated)
      text = ''
      previewItems = []
      showPreview = false
      manualOverrides = {}
      alert(`${res.registered} 件のNGを登録しました`)
    } catch (e) {
      errorMsg.set(e.message)
    } finally {
      loading = false
    }
  }

  function clearAll() {
    text = ''
    previewItems = []
    showPreview = false
    manualOverrides = {}
  }
</script>

<div class="glass-panel rounded-2xl overflow-hidden">
  <div class="px-6 py-4 border-b flex items-center justify-between"
       style="border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.2);">
    <h2 class="text-sm font-bold uppercase tracking-widest" style="color: var(--color-outline);">
      {panelTitle}
    </h2>
    <div class="flex items-center gap-2">
      <label for="year-{shiftType}" class="text-xs font-semibold" style="color: var(--color-outline);">基準年</label>
      <input
        id="year-{shiftType}"
        type="number"
        bind:value={year}
        class="w-20 px-2 py-1 rounded-lg text-sm border text-center focus:outline-none"
        style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
      />
    </div>
  </div>

  <div class="px-6 py-4 space-y-3" style="background: rgba(255,255,255,0.1);">
    <div class="flex flex-col gap-1">
      <label for="paste-{shiftType}" class="text-xs font-semibold uppercase tracking-widest" style="color: var(--color-outline);">
        貼り付けテキスト（名前と日付をそのまま貼り付け）
      </label>
      <textarea
        id="paste-{shiftType}"
        bind:value={text}
        rows="6"
        placeholder={placeholder}
        class="w-full px-3 py-2 rounded-lg text-sm border focus:outline-none font-mono leading-relaxed"
        style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7); resize: vertical;"
      ></textarea>
      <p class="text-[11px]" style="color: var(--color-outline);">
        ※ 区切り（カンマ・スペース・改行）の揺れ、月省略、全角数字・「日」付きなどに対応しています
      </p>
    </div>

    <div class="flex gap-2 justify-end">
      <button
        on:click={clearAll}
        class="px-4 py-2 rounded-lg text-sm font-semibold border transition-all hover:bg-white/30"
        style="border-color: var(--color-outline-variant); color: var(--color-on-surface-variant);"
      >
        クリア
      </button>
      <button
        on:click={parsePreview}
        disabled={loading || !text.trim()}
        class="px-5 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
        style="background: var(--color-primary);"
      >
        {#if loading}解析中...{:else}プレビュー{/if}
      </button>
    </div>
  </div>

  {#if showPreview}
    <div class="border-t" style="border-color: rgba(255,255,255,0.2);">
      <div class="px-6 py-3 flex items-center justify-between" style="background: rgba(255,255,255,0.15);">
        <h3 class="text-xs font-bold uppercase tracking-widest" style="color: var(--color-outline);">
          解析結果（{resolvedItems.length}名 / {resolvedItems.reduce((a, b) => a + b.dates.length, 0)}日）
        </h3>
        <button
          on:click={register}
          disabled={loading || resolvedItems.length === 0 || unresolvedItems.length > 0}
          class="px-4 py-1.5 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
          style="background: var(--color-primary-container);"
        >
          {#if loading}登録中...{:else}一括登録{/if}
        </button>
      </div>

      {#if unresolvedItems.length > 0}
        <div class="px-6 py-2 text-[11px] font-semibold" style="background: rgba(255,200,200,0.25); color: var(--color-error);">
          <span class="material-symbols-outlined text-xs align-middle">warning</span>
          未解決の名前があります。プルダウンで正しい名前を選択してください。
        </div>
      {/if}

      {#if previewItems.length === 0}
        <div class="px-6 py-6 text-center text-sm" style="color: var(--color-outline);">
          有効なデータが検出されませんでした。テキスト形式を確認してください。
        </div>
      {:else}
        <div class="max-h-64 overflow-y-auto">
          {#each resolvedItems as item, idx}
            <div class="px-6 py-2.5 flex items-start gap-3 hover:bg-white/20 transition-colors"
                 style="border-bottom: 1px solid rgba(255,255,255,0.08);">
              <div class="w-32 shrink-0">
                {#if item.resolvedName}
                  <span class="text-sm font-semibold" style="color: var(--color-on-surface);">
                    {#if item.method === 'manual' || item.method === 'exact'}
                      {item.resolvedName}
                    {:else}
                      {item.person_name} <span class="text-[10px]" style="color: var(--color-outline);">→</span> {item.resolvedName}
                    {/if}
                  </span>
                  {#if item.method === 'fuzzy'}
                    <span class="ml-1 text-[10px] px-1 py-0.5 rounded" style="background: rgba(255,200,100,0.3); color: var(--color-on-surface-variant);">類似</span>
                  {/if}
                {:else}
                  <span class="text-sm font-semibold" style="color: var(--color-error);">{item.person_name}</span>
                  <span class="ml-1 text-[10px]" style="color: var(--color-error);">(未登録)</span>
                {/if}
              </div>

              <!-- 手動選択プルダウン（未解決 or 修正したい場合） -->
              <div class="shrink-0">
                <select
                  class="px-2 py-1 rounded-lg text-[11px] border focus:outline-none"
                  style="border-color: var(--color-outline-variant); background: rgba(255,255,255,0.7);"
                  on:change={(e) => {
                    manualOverrides = { ...manualOverrides, [item.person_name]: e.target.value || null }
                  }}
                >
                  <option value="">{item.resolvedName ? '変更...' : '名前を選択'}</option>
                  {#each memberNames as name}
                    <option value={name} selected={item.resolvedName === name}>{name}</option>
                  {/each}
                </select>
              </div>

              <div class="flex-1 flex flex-wrap gap-1">
                {#each item.dates as d}
                  <span class="inline-block px-2 py-0.5 rounded-md text-[11px] font-medium"
                        style="background: rgba(255,255,255,0.3); color: var(--color-on-surface-variant);">
                    {d}
                  </span>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>
