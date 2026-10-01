function PageHeader({ eyebrow, title, description }) {
  return (
    <header className="space-y-2">
      {eyebrow ? (
        <p className="text-sm font-medium tracking-wide text-brand uppercase">{eyebrow}</p>
      ) : null}
      <h1 className="text-3xl font-semibold tracking-tight text-ink">{title}</h1>
      {description ? (
        <p className="max-w-3xl text-sm leading-6 text-muted sm:text-base">{description}</p>
      ) : null}
    </header>
  )
}

export default PageHeader
