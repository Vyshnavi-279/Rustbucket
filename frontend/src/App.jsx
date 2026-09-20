import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import SubmitPage from './pages/SubmitPage'

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <nav className="flex items-center gap-6 bg-white px-6 py-3 shadow">
        <span className="text-xl font-bold text-orange-600">Rustbucket</span>
        <NavLink to="/" className="hover:underline">Scan</NavLink>
        <NavLink to="/history" className="hover:underline">History</NavLink>
      </nav>
      <main className="mx-auto max-w-5xl p-6">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<SubmitPage />} />
          <Route path="/scans/:scanId" element={<h1>Results page (coming soon)</h1>} />
          <Route path="/history" element={<h1>History (coming soon)</h1>} />
          <Route path="/history/:repoId" element={<h1>Repo history (coming soon)</h1>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}