const BASE = '/api'

async function request(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`${res.status}: ${detail}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  getMembers: () => request('GET', '/members'),
  createMember: (member) => request('POST', '/members', member),
  deleteMember: (name) => request('DELETE', `/members/${encodeURIComponent(name)}`),
  updateMemberFlags: (name, flags) => request('PATCH', `/members/${encodeURIComponent(name)}/flags`, flags),
  getNgEntries: () => request('GET', '/ng_entries'),
  createNgEntry: (entry) => request('POST', '/ng_entries', entry),
  deleteNgEntry: (index) => request('DELETE', `/ng_entries/${index}`),
  parseNgBulk: (text, defaultYear, shiftType) => request('POST', '/ng_entries/bulk_parse', { text, default_year: defaultYear, shift_type: shiftType }),
  registerNgBulk: (items, shiftType) => request('POST', '/ng_entries/bulk', { items, shift_type: shiftType }),
  getHistory: () => request('GET', '/history'),
  getHistoryState: () => request('GET', '/history/state'),
  getHistorySource: () => request('GET', '/history/source'),
  generateSchedule: (payload) => request('POST', '/schedule/generate', payload),
  exportEntries: async (entries) => {
    const res = await fetch(BASE + '/history/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entries),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.blob()
  },
  exportHistory: async () => {
    const res = await fetch(BASE + '/history/export')
    if (!res.ok) throw new Error(await res.text())
    return res.blob()
  },
}
