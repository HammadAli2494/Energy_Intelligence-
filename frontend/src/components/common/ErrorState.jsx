function ErrorState({ title, message }) {
  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      role="alert"
    >
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-red-700">{message}</p>
    </div>
  )
}

export default ErrorState
