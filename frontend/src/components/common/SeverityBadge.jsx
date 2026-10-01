function SeverityBadge({ severity }) {
  const styles =
    severity === 'high'
      ? 'bg-red-100 text-red-800'
      : 'bg-amber-100 text-amber-900'
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize ${styles}`}>
      {severity}
    </span>
  )
}

export default SeverityBadge
