export function formatMw(value, digits = 0) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return `${Number(value).toLocaleString('en-US', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })} MW`
}

export function formatNumber(value, digits = 2) {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString('en-US', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
}

export function formatTimestamp(iso) {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return `${date.toLocaleString('en-GB', {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })} UTC`
}

export function weekdayLabel(day) {
  return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][day] ?? String(day)
}

export function monthLabel(month) {
  return (
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][
      month - 1
    ] ?? String(month)
  )
}

export function chartTime(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  return date.toLocaleString('en-GB', {
    timeZone: 'UTC',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
  })
}
