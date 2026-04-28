import { writable } from 'svelte/store'
import { api } from './api.js'

export const members = writable([])
export const ngEntries = writable([])
export const scheduleResult = writable(null)
/** カレンダーと同じ表示データ（編集反映）＋期間。当番統計ページ用 */
export const scheduleView = writable({ entries: null, rangeStart: '', rangeEnd: '' })
export const warnings = writable([])
export const loading = writable(false)
export const errorMsg = writable('')

/** 手入力スタッフは API 経由で previous_data と同様 exe 横（開発時は .docs）に永続化する */
export const manualMembers = writable([])

let _manualPersistSkip = true

manualMembers.subscribe((v) => {
  if (_manualPersistSkip || typeof window === 'undefined') return
  api.saveManualStaff(v).catch((e) => errorMsg.set(String(e.message ?? e)))
})

/**
 * アプリ起動時に呼ぶ。サーバから手入力スタッフ一覧を読み込み、以降の変更を自動保存する。
 */
export async function initManualStaff() {
  _manualPersistSkip = true
  try {
    const data = await api.getManualStaff()
    manualMembers.set(Array.isArray(data) ? data : [])
  } catch (e) {
    console.warn('initManualStaff:', e)
    manualMembers.set([])
  } finally {
    _manualPersistSkip = false
  }
}
