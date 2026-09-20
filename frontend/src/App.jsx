import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import SubmitPage from './pages/SubmitPage'
import ResultsPage from './pages/ResultsPage'
import HistoryListPage from './pages/HistoryListPage'
import RepoHistoryPage from './pages/RepoHistoryPage'
import NotFoundPage from './pages/NotFoundPage'

const linkClass = ({ isActive }) =>
  `rounded px-2 py-1 hover:underline ${isActive ? 'font-semibold text-orange-700' : 'text-slate-700'}`

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-10 focus:rounded focus:bg-white focus:px-3 focus:py-2">Skip to content</a>
      <nav aria-label="Main" className="flex flex-wrap items-center gap-x-6 gap-y-2 bg-white px-4 py-3 shadow sm:px-6">
        <span className="text-xl font-bold text-orange-700">Rustbucket</span>
        <NavLink to="/" end className={linkClass}>Scan</NavLink>
        <NavLink to="/history" className={linkClass}>History</NavLink>
      </nav>
      <main id="main" className="mx-auto max-w-5xl p-4 sm:p-6">{children}</main>
    </div>
  )
}

function AppRoutes() {
  const location = useLocation()
  // key resets the inner boundary when the user navigates to another page
  return (
    <ErrorBoundary key={location.pathname}>
      <Routes>
        <Route path="/" element={<SubmitPage />} />
        <Route path="/scans/:scanId" element={<ResultsPage />} />
        <Route path="/history" element={<HistoryListPage />} />
        <Route path="/history/:repoId" element={<RepoHistoryPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </ErrorBoundary>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Layout>
          <AppRoutes />
        </Layout>
      </BrowserRouter>
    </ErrorBoundary>
  )
}