import { X, FileText, ExternalLink, FolderOpen, Check, Database } from 'lucide-react'
import useStore from '../../store/store'
import { formatMatchScore } from '../../utils/score'

/**
 * ContextPanel - Collapsible right panel
 * Shows collection filters, active sources, and quick tips
 */
export default function ContextPanel() {
    const {
        setContextPanelOpen,
        activeDocument,
        activeSources,
        collections,
        selectedCollections,
        toggleCollectionFilter,
        clearCollectionFilters
    } = useStore()

    return (
        <aside className="w-context flex flex-col bg-aegis-rag-bg-panel border-l border-aegis-rag-border">
            {/* Header */}
            <div className="h-14 px-4 flex items-center justify-between border-b border-aegis-rag-border">
                <h2 className="font-semibold text-aegis-rag-text-primary">Context</h2>
                <button
                    onClick={() => setContextPanelOpen(false)}
                    className="btn-icon"
                >
                    <X size={18} />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-6">
                {/* Collection Filter - MOVED TO TOP for visibility */}
                <section>
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-xs font-medium text-aegis-rag-text-muted uppercase tracking-wider">
                            Search In Collections
                        </h3>
                    </div>

                    <div className="space-y-1.5">
                        {/* All Documents Option */}
                        <button
                            onClick={clearCollectionFilters}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-fast text-left ${selectedCollections.length === 0
                                ? 'bg-aegis-rag-accent/20 border border-aegis-rag-accent/40'
                                : 'bg-aegis-rag-bg-card border border-aegis-rag-border hover:border-aegis-rag-accent/30'
                                }`}
                        >
                            <div className={`w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 ${selectedCollections.length === 0
                                ? 'bg-aegis-rag-accent'
                                : 'bg-aegis-rag-bg-elevated border border-aegis-rag-border'
                                }`}>
                                {selectedCollections.length === 0 && <Check size={12} className="text-aegis-rag-bg-app" />}
                            </div>
                            <Database size={16} className={selectedCollections.length === 0 ? 'text-aegis-rag-accent' : 'text-aegis-rag-text-muted'} />
                            <span className={`text-sm ${selectedCollections.length === 0 ? 'text-aegis-rag-accent font-medium' : 'text-aegis-rag-text-primary'
                                }`}>
                                All Documents
                            </span>
                        </button>

                        {/* Collection options */}
                        {collections.length > 0 && collections.map((collection) => {
                            const isSelected = selectedCollections.includes(collection)
                            return (
                                <button
                                    key={collection}
                                    onClick={() => toggleCollectionFilter(collection)}
                                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-fast text-left ${isSelected
                                        ? 'bg-aegis-rag-accent/20 border border-aegis-rag-accent/40'
                                        : 'bg-aegis-rag-bg-card border border-aegis-rag-border hover:border-aegis-rag-accent/30'
                                        }`}
                                >
                                    <div className={`w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 ${isSelected
                                        ? 'bg-aegis-rag-accent'
                                        : 'bg-aegis-rag-bg-elevated border border-aegis-rag-border'
                                        }`}>
                                        {isSelected && <Check size={12} className="text-aegis-rag-bg-app" />}
                                    </div>
                                    <FolderOpen size={16} className={isSelected ? 'text-aegis-rag-accent' : 'text-aegis-rag-text-muted'} />
                                    <span className={`text-sm truncate ${isSelected ? 'text-aegis-rag-accent font-medium' : 'text-aegis-rag-text-primary'
                                        }`}>
                                        {collection}
                                    </span>
                                </button>
                            )
                        })}

                        {collections.length === 0 && (
                            <p className="text-xs text-aegis-rag-text-muted text-center py-2">
                                No collections created yet
                            </p>
                        )}
                    </div>
                </section>

                {/* Active Document */}
                {activeDocument && (
                    <section>
                        <h3 className="text-xs font-medium text-aegis-rag-text-muted uppercase tracking-wider mb-3">
                            Active Document
                        </h3>
                        <div className="card p-4">
                            <div className="flex items-start gap-3">
                                <div className="w-10 h-10 rounded-xl bg-aegis-rag-bg-elevated flex items-center justify-center flex-shrink-0">
                                    <FileText size={20} className="text-aegis-rag-accent" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-aegis-rag-text-primary truncate">
                                        {activeDocument.name}
                                    </p>
                                    <p className="text-xs text-aegis-rag-text-muted mt-1">
                                        {activeDocument.type} • {activeDocument.pages} pages
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>
                )}

                {/* Sources */}
                <section>
                    <h3 className="text-xs font-medium text-aegis-rag-text-muted uppercase tracking-wider mb-3">
                        Referenced Sources
                    </h3>

                    {activeSources.length > 0 ? (
                        <div className="space-y-2">
                            {activeSources.map((source, index) => {
                                // Handle both backend and mapped formats
                                const fullPath = source.file || source.filename || ''
                                const location = source.location
                                const score = source.similarity || source.score
                                const matchScore = formatMatchScore(score)
                                const docType = source.type || 'document'

                                // Extract just the filename for display
                                const displayName = fullPath ? fullPath.replace(/\\/g, '/').split('/').pop() : 'Unknown'

                                // Open file in new tab
                                const handleOpenFile = () => {
                                    if (fullPath) {
                                        // Convert to file:// URL (handle Windows paths)
                                        const fileUrl = `file:///${fullPath.replace(/\\/g, '/')}`
                                        window.open(fileUrl, '_blank')
                                    }
                                }

                                return (
                                    <button
                                        key={index}
                                        onClick={handleOpenFile}
                                        className="w-full text-left card p-3 hover:bg-aegis-rag-bg-hover transition-fast group"
                                        title={`Open: ${fullPath}`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-aegis-rag-text-primary truncate">
                                                    {displayName}
                                                </p>
                                                <p className="text-xs text-aegis-rag-text-muted mt-0.5">
                                                    {docType}
                                                    {location && ` • ${location}`}
                                                    {matchScore && ` • ${matchScore}`}
                                                </p>
                                            </div>
                                            <ExternalLink
                                                size={14}
                                                className="text-aegis-rag-text-muted group-hover:text-aegis-rag-accent transition-fast flex-shrink-0 ml-2"
                                            />
                                        </div>
                                    </button>
                                )
                            })}
                        </div>
                    ) : (
                        <div className="card p-6 text-center">
                            <p className="text-sm text-aegis-rag-text-muted">
                                Sources will appear here when you ask questions
                            </p>
                        </div>
                    )}
                </section>

                {/* Quick Info */}
                <section>
                    <h3 className="text-xs font-medium text-aegis-rag-text-muted uppercase tracking-wider mb-3">
                        Quick Tips
                    </h3>
                    <div className="card p-4 space-y-3">
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-lg bg-aegis-rag-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-aegis-rag-accent text-xs font-bold">1</span>
                            </div>
                            <p className="text-sm text-aegis-rag-text-secondary">
                                Select collections above to filter your search
                            </p>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-lg bg-aegis-rag-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-aegis-rag-accent text-xs font-bold">2</span>
                            </div>
                            <p className="text-sm text-aegis-rag-text-secondary">
                                No selection = search all documents
                            </p>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="w-6 h-6 rounded-lg bg-aegis-rag-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-aegis-rag-accent text-xs font-bold">3</span>
                            </div>
                            <p className="text-sm text-aegis-rag-text-secondary">
                                Click on sources to view original context
                            </p>
                        </div>
                    </div>
                </section>
            </div>
        </aside>
    )
}
