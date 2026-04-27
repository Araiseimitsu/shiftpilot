/** config/settings.yaml の schedule.night_shift_start_weekday（0=月）に合わせる */
export const NIGHT_WEEK_START_PY_WEEKDAY = 0

function dateOf(e) {
  if (!e || e.date == null) return ''
  if (typeof e.date === 'string') return e.date
  if (e.date && typeof e.date === 'object' && typeof e.date.toISOString === 'function') {
    return e.date.toISOString().slice(0, 10)
  }
  return String(e.date).slice(0, 10)
}

function toPyWeekday(dateStr) {
  const d = new Date(`${dateStr}T12:00:00`)
  return (d.getDay() + 6) % 7
}

function weekStartDateStr(dateStr, startWeekdayPy) {
  const d = new Date(`${dateStr}T12:00:00`)
  const pywd = toPyWeekday(dateStr)
  const back = (pywd - startWeekdayPy + 7) % 7
  d.setDate(d.getDate() - back)
  return d.toISOString().slice(0, 10)
}

function minGapDaysSortedDateStrs(sortedYmd) {
  if (sortedYmd.length < 2) return null
  let minG = Infinity
  for (let i = 1; i < sortedYmd.length; i++) {
    const a = new Date(`${sortedYmd[i - 1]}T12:00:00`)
    const b = new Date(`${sortedYmd[i]}T12:00:00`)
    const diff = Math.round((b - a) / 86400000)
    if (diff < minG) minG = diff
  }
  return minG === Infinity ? null : minG
}

/**
 * 表示中のシフト一覧から当番決め用の統計を算出する。
 * 夜勤は「週ブロック」を1イベントとして間隔に含め、日勤は各日付を1イベントとする。
 */
export function computeScheduleStats(entries, nightWeekStartPy = NIGHT_WEEK_START_PY_WEEKDAY) {
  if (!entries?.length) return null

  let minD = null
  let maxD = null
  for (const e of entries) {
    const ds = dateOf(e)
    if (!ds) continue
    if (minD == null || ds < minD) minD = ds
    if (maxD == null || ds > maxD) maxD = ds
  }

  const byName = new Map()

  for (const e of entries) {
    const name = e.person_name
    if (!name) continue
    if (!byName.has(name)) {
      byName.set(name, {
        totalSlots: 0,
        day1: 0,
        day2: 0,
        nightDays: 0,
        nightWeekAnchors: new Set(),
        mergedEventKeys: new Set(),
        dayDates: [],
      })
    }
    const row = byName.get(name)
    row.totalSlots += 1
    const ds = dateOf(e)
    if (e.shift_category === 'Night') {
      row.nightDays += 1
      const anchor = weekStartDateStr(ds, nightWeekStartPy)
      row.nightWeekAnchors.add(anchor)
      row.mergedEventKeys.add(`N:${anchor}`)
    } else {
      if (e.shift_index === 1) row.day1 += 1
      else row.day2 += 1
      row.dayDates.push(ds)
      row.mergedEventKeys.add(`D:${ds}`)
    }
  }

  const people = []
  for (const [name, row] of byName) {
    const mergedDates = [...row.mergedEventKeys]
      .map((k) => k.slice(2))
      .sort((a, b) => a.localeCompare(b))
    const minMergedGap = minGapDaysSortedDateStrs(mergedDates)

    const dayUnique = [...new Set(row.dayDates)].sort((a, b) => a.localeCompare(b))
    const minDayOnlyGap = minGapDaysSortedDateStrs(dayUnique)

    people.push({
      name,
      totalSlots: row.totalSlots,
      day1: row.day1,
      day2: row.day2,
      nightDays: row.nightDays,
      nightWeeks: row.nightWeekAnchors.size,
      minMergedGapDays: mergedDates.length < 2 ? null : minMergedGap,
      minDayOnlyGapDays: dayUnique.length < 2 ? null : minDayOnlyGap,
    })
  }

  people.sort((a, b) => a.name.localeCompare(b.name, 'ja'))

  const totalSlots = entries.length
  const assignedNames = new Set(people.map((p) => p.name))

  return {
    range: { start: minD, end: maxD },
    totalSlots,
    people,
    assignedCount: people.length,
    assignedNames,
  }
}
