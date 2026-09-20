import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    console.error('UI error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" className="mx-auto max-w-md rounded-2xl border border-red-300 bg-red-50 p-6 text-center">
          <h1 className="text-xl font-bold text-red-800">Something went wrong</h1>
          <p className="mt-2 text-red-800">The page hit an unexpected error. Try reloading it.</p>
          <div className="mt-4 flex justify-center gap-3">
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded-lg bg-orange-700 px-4 py-2 font-semibold text-white hover:bg-orange-800"
            >
              Reload page
            </button>
            <a href="/" className="rounded-lg border border-slate-300 bg-white px-4 py-2 font-semibold hover:bg-slate-100">
              Go home
            </a>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}