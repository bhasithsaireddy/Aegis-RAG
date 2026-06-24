import { Component } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

/**
 * ErrorBoundary — catches unhandled React errors and renders a fallback UI
 * instead of a blank/crashed screen.
 */
export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null, errorInfo: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        console.error('[ErrorBoundary] Unhandled error:', error, errorInfo)
        this.setState({ errorInfo })
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null })
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="h-screen flex items-center justify-center bg-aegis-rag-bg-app">
                    <div className="max-w-md w-full mx-4 p-8 card text-center space-y-4">
                        <AlertTriangle className="mx-auto text-amber-500" size={40} />
                        <h1 className="text-xl font-semibold text-aegis-rag-text-primary">
                            Something went wrong
                        </h1>
                        <p className="text-sm text-aegis-rag-text-secondary">
                            An unexpected error occurred in the UI. Your data is safe.
                        </p>
                        {this.state.error && (
                            <pre className="text-xs text-left bg-aegis-rag-bg-elevated rounded-lg p-3 overflow-auto max-h-40 text-aegis-rag-text-muted">
                                {this.state.error.message}
                            </pre>
                        )}
                        <button
                            onClick={this.handleReset}
                            className="btn-primary flex items-center gap-2 mx-auto"
                        >
                            <RefreshCw size={14} />
                            Try Again
                        </button>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}
