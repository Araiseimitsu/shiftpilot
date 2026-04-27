import { writable } from 'svelte/store'

export const members = writable([])
export const ngEntries = writable([])
export const scheduleResult = writable(null)
/** カレンダーと同じ表示データ（編集反映）＋期間。当番統計ページ用 */
export const scheduleView = writable({ entries: null, rangeStart: '', rangeEnd: '' })
export const warnings = writable([])
export const loading = writable(false)
export const errorMsg = writable('')
