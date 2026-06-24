import { useEffect, useCallback } from 'react'
import useStore from './store/store'
import api from './services/api'
import useKeyboardShortcuts from './hooks/useKeyboardShortcuts'
import ErrorBoundary from './components/ErrorBoundary'

// Layout Components
import TopBar from './components/layout/TopBar'
import Sidebar from './components/layout/Sidebar'
import ContextPanel from './components/layout/ContextPanel'

// Views
import Dashboard from './views/Dashboard'
import QueryWorkspace from './views/QueryWorkspace'
import CollectionsManager from './views/CollectionsManager'
import SettingsView from './views/SettingsView'

// Feature Components
import IngestionPanel from './components/ingestion/IngestionPanel'

export default function App() {
  const {
    activeView,
    setActiveView,
    isContextPanelOpen,
    theme,
    themePreference,
    syncTheme,
    setBackendStatus,
    setSystemInfo,
    setCollections,
    setDocuments,
    toggleIngestion
  } = useStore()

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
  }, [theme])

  useEffect(() => {
    if (typeof window === 'undefined' || themePreference !== 'system') {
      return undefined
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)')
    const applySystemTheme = () => {
      syncTheme(mediaQuery.matches ? 'light' : 'dark')
    }

    applySystemTheme()

    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', applySystemTheme)
      return () => mediaQuery.removeEventListener('change', applySystemTheme)
    }

    mediaQuery.addListener(applySystemTheme)
    return () => mediaQuery.removeListener(applySystemTheme)
  }, [themePreference, syncTheme])

  // Backend health check and data fetch
  const checkBackend = useCallback(async () => {
    try {
      const isHealthy = await api.checkHealth()
      setBackendStatus(isHealthy ? 'connected' : 'disconnected')

      if (isHealthy) {
        // Fetch stats
        try {
          const stats = await api.getStats()
          setSystemInfo({
            totalChunks: stats.total_chunks || 0,
            totalDocuments: stats.total_documents || 0,
          })
        } catch (e) {
          console.warn('Stats not available:', e.message)
        }

        // Fetch model status
        try {
          const modelStatus = await api.getModelStatus()
          setSystemInfo({
            llmModel: modelStatus.llm?.model || 'Unknown',
            llmAvailable: modelStatus.llm?.available ?? false,
            visionModel: modelStatus.vision?.model || 'Unknown',
            visionAvailable: modelStatus.vision?.available ?? false,
            embeddingModel: modelStatus.embedding?.model || 'Unknown',
            embeddingAvailable: modelStatus.embedding?.available ?? false,
          })
        } catch (e) {
          console.warn('Model status not available:', e.message)
        }

        // Fetch collections (backend returns array of strings)
        try {
          const collections = await api.getCollections()
          setCollections(collections || [])
        } catch (e) {
          console.warn('Collections not available:', e.message)
        }

        // Fetch documents and map to frontend format
        try {
          const docsResponse = await api.getDocuments()
          const mappedDocs = (docsResponse || []).map(doc => ({
            id: doc.document_id,
            document_id: doc.document_id,
            name: doc.source_file,
            source_file: doc.source_file,
            doc_type: doc.doc_type,
            collections: doc.collections || [],
            chunks: doc.chunk_count,
            created_at: doc.created_at,
          }))
          setDocuments(mappedDocs)
        } catch (e) {
          console.warn('Documents not available:', e.message)
        }
      }
    } catch {
      setBackendStatus('disconnected')
    }
  }, [setBackendStatus, setSystemInfo, setCollections, setDocuments])

  // Initial check and polling
  useEffect(() => {
    checkBackend()
    const interval = setInterval(checkBackend, 10000) // Check every 10s
    return () => clearInterval(interval)
  }, [checkBackend])

  // Global keyboard shortcuts
  useKeyboardShortcuts({
    'ctrl+,': () => setActiveView('settings'),
    'ctrl+i': () => toggleIngestion(),
    'ctrl+k': () => setActiveView('chat'),
    'ctrl+d': () => setActiveView('dashboard'),
    'ctrl+l': () => setActiveView('documents'),
  })

  // Render active view
  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard />
      case 'chat':
        return <QueryWorkspace />
      case 'documents':
        return <CollectionsManager />
      case 'settings':
        return <SettingsView />
      default:
        return <QueryWorkspace />
    }
  }

  return (
    <ErrorBoundary>
      <div className="h-screen flex flex-col overflow-hidden bg-aegis-rag-bg-app">
        {/* Top Bar - Slim status bar */}
        <TopBar />

        {/* Main Three-Pane Layout */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Navigation Sidebar */}
          <Sidebar />

          {/* Center: Main Workspace (Dynamic View) */}
          {renderView()}

          {/* Right: Context Panel (Collapsible) */}
          {isContextPanelOpen && <ContextPanel />}
        </div>

        {/* Modal Overlays */}
        <IngestionPanel />
      </div>
    </ErrorBoundary>
  )
}
