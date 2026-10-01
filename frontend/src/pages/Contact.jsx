import { useState } from 'react'
import Disclaimer from '../components/common/Disclaimer'
import ErrorState from '../components/common/ErrorState'
import PageHeader from '../components/common/PageHeader'
import { submitContact } from '../services/api'

const emptyForm = {
  name: '',
  email: '',
  subject: '',
  message: '',
}

function Contact() {
  const [form, setForm] = useState(emptyForm)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function update(field) {
    return (event) => setForm((current) => ({ ...current, [field]: event.target.value }))
  }

  function onSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setStatus('')
    submitContact(form)
      .then(() => {
        setStatus('Message stored.')
        setForm(emptyForm)
      })
      .catch((err) => setError(err.message))
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Inbox"
        title="Contact"
        description="Messages are stored only if MongoDB is configured on the API. Without Atlas, the server returns 503."
      />
      <Disclaimer>
        Do not send passwords, API keys, or personal data you would not want stored in a
        student project database.
      </Disclaimer>

      <form
        onSubmit={onSubmit}
        className="max-w-xl space-y-4 rounded-xl border border-line bg-white p-5"
      >
        <label className="block text-sm">
          <span className="font-medium text-ink">Name</span>
          <input
            required
            minLength={2}
            value={form.name}
            onChange={update('name')}
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-ink">Email</span>
          <input
            required
            type="email"
            value={form.email}
            onChange={update('email')}
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-ink">Subject</span>
          <input
            required
            minLength={3}
            value={form.subject}
            onChange={update('subject')}
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-ink">Message</span>
          <textarea
            required
            minLength={10}
            rows={5}
            value={form.message}
            onChange={update('message')}
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
          />
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-60"
        >
          {submitting ? 'Sending…' : 'Send message'}
        </button>
        {status ? <p className="text-sm text-brand-dark">{status}</p> : null}
        {error ? <ErrorState title="Could not store the message" message={error} /> : null}
      </form>
    </div>
  )
}

export default Contact
