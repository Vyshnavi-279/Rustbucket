import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import SubmitPage from './pages/SubmitPage'
import ResultsPage from './pages/ResultsPage'
import HistoryListPage from './pages/HistoryListPage'
import RepoHistoryPage from './pages/RepoHistoryPage'

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
          <Route path="/scans/:scanId" element={<ResultsPage />} />
          <Route path="/history" element={<HistoryListPage />} />
          <Route path="/history/:repoId" element={<RepoHistoryPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}