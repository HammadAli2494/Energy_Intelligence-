function LoadingSpinner({ label = 'Loading' }) {
  return (
    <div className="flex items-center gap-3 text-sm text-muted" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-brand" />
      <span>{label}</span>
    </div>
  )
}

export default LoadingSpinner
