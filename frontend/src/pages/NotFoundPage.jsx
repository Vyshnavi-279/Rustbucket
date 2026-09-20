import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-md rounded-2xl bg-white p-8 text-center shadow">
      <p className="text-5xl font-bold text-slate-500" aria-hidden="true">
        404
      </p>
      <h1 className="mt-2 text-2xl font-bold">Page not found</h1>
      <p className="mt-2 text-slate-600">The page you are looking for does not exist.</p>
      <Link
        to="/"
        className="mt-4 inline-block rounded-lg bg-orange-700 px-4 py-2 font-semibold text-white hover:bg-orange-800"
      >
        Back to Scan
      </Link>
    </div>
  )
}