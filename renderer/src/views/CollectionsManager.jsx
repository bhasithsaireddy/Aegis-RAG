import { useState, useEffect, useCallback } from 'react'
import { FolderOpen, Search, Grid, List, FileText, Image, Mic, Trash2, Eye, Plus, Loader2, RefreshCw } from 'lucide-react'
import useStore from '../store/store'
import api from '../services/api'

/**
 * CollectionsManager - Document library view
 * Displays ingested documents with search and delete operations
 */
export default function CollectionsManager() {
    const { documents, setDocuments, toggleIngestion, setCollections } = useStore()
    const [viewMode, setViewMode] = useState('grid')
    const [newCollection, setNewCollection] = useState('')
    const [searchQuery, setSearchQuery] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [deletingId, setDeletingId] = useState(null)

    const fetchData = useCallback(async () => {
        setIsLoading(true)
        try {
            const docsResponse = await api.getDocuments()
            const mappedDocs = (docsResponse || []).map((doc) => ({
                id: doc.document_id,
                document_id: doc.document_id,
                name: doc.source_file,
                source_file: doc.source_file,
                doc_type: doc.doc_type,
                chunks: doc.chunk_count,
                created_at: doc.created_at,
            }))

            setDocuments(mappedDocs)
        } catch (err) {
            console.error('Failed to fetch data:', err)
        } finally {
            setIsLoading(false)
        }
    }, [setDocuments])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const getFileName = (path) => {
        if (!path) return 'Unknown'
        const parts = path.replace(/\\/g, '/').split('/')
        return parts[parts.length - 1] || path
    }

    const docsList = Array.isArray(documents) ? documents : []
    const filteredDocuments = docsList.filter((doc) => {
        const fileName = getFileName(doc.name)
        return fileName?.toLowerCase().includes(searchQuery.toLowerCase())
    })

    const handleDeleteDocument = async (documentId) => {
        if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
            return
        }

        setDeletingId(documentId)
        try {
            await api.deleteDocument(documentId)
            setDocuments(documents.filter((doc) => doc.document_id !== documentId))
        } catch (err) {
            console.error('Failed to delete document:', err)
            alert(`Failed to delete document: ${err.message}`)
        } finally {
            setDeletingId(null)
        }
    }

    const getFileIcon = (docType) => {
        switch (docType?.toLowerCase()) {
            case 'pdf': return { icon: FileText, color: 'text-zinc-200', bg: 'bg-zinc-400/10' }
            case 'docx':
            case 'doc': return { icon: FileText, color: 'text-zinc-300', bg: 'bg-zinc-400/10' }
            case 'image':
            case 'png':
            case 'jpg':
            case 'jpeg': return { icon: Image, color: 'text-zinc-300', bg: 'bg-zinc-400/10' }
            case 'audio':
            case 'voice':
            case 'wav':
            case 'mp3': return { icon: Mic, color: 'text-zinc-300', bg: 'bg-zinc-400/10' }
            default: return { icon: FileText, color: 'text-aegis-rag-text-muted', bg: 'bg-aegis-rag-bg-elevated' }
        }
    }

    const formatDate = (date) => {
        if (!date) return 'Unknown'
        return new Date(date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        })
    }

    return (
        <main className="flex-1 flex flex-col bg-aegis-rag-bg-app overflow-hidden">
            <div className="px-6 py-4 border-b border-aegis-rag-border flex-shrink-0">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <FolderOpen size={24} className="text-aegis-rag-accent" />
                        <div>
                            <h1 className="text-xl font-semibold text-aegis-rag-text-primary">Documents</h1>
                            <p className="text-sm text-aegis-rag-text-muted">
                                {docsList.length} document{docsList.length !== 1 ? 's' : ''} in your workspace
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button onClick={fetchData} disabled={isLoading} className="btn-icon" title="Refresh">
                            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
                        </button>
                        <div className="flex items-center gap-2">
                            <input
                                type="text"
                                placeholder="New collection name"
                                value={newCollection}
                                onChange={(e) => setNewCollection(e.target.value)}
                                className="input px-3 py-2 mr-2"
                                aria-label="New collection name"
                            />
                            <button
                                onClick={async () => {
                                    const name = (newCollection || '').trim()
                                    if (!name) return alert('Please enter a collection name')
                                    try {
                                        await api.createCollection(name)
                                        const cols = await api.getCollections()
                                        setCollections(cols || [])
                                        setNewCollection('')
                                    } catch (err) {
                                        console.error('Failed to create collection:', err)
                                        alert('Failed to create collection: ' + (err.message || err))
                                    }
                                }}
                                className="btn-secondary flex items-center gap-2"
                            >
                                <Plus size={16} />
                                <span>Create</span>
                            </button>
                            <button onClick={toggleIngestion} className="btn-primary flex items-center gap-2">
                                <Plus size={18} />
                                <span>Add Documents</span>
                            </button>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex-1 relative">
                        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-aegis-rag-text-muted" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search documents..."
                            className="input pl-11"
                        />
                    </div>

                    <div className="flex items-center bg-aegis-rag-bg-card rounded-xl border border-aegis-rag-border p-1">
                        <button
                            onClick={() => setViewMode('grid')}
                            className={`p-2 rounded-lg transition-fast ${viewMode === 'grid'
                                ? 'bg-aegis-rag-accent text-aegis-rag-bg-app'
                                : 'text-aegis-rag-text-muted hover:text-aegis-rag-text-primary'
                                }`}
                        >
                            <Grid size={18} />
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            className={`p-2 rounded-lg transition-fast ${viewMode === 'list'
                                ? 'bg-aegis-rag-accent text-aegis-rag-bg-app'
                                : 'text-aegis-rag-text-muted hover:text-aegis-rag-text-primary'
                                }`}
                        >
                            <List size={18} />
                        </button>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
                {isLoading && documents.length === 0 ? (
                    <div className="h-full flex items-center justify-center">
                        <Loader2 size={32} className="animate-spin text-aegis-rag-accent" />
                    </div>
                ) : filteredDocuments.length === 0 ? (
                    <EmptyLibrary onUpload={toggleIngestion} hasDocuments={documents.length > 0} />
                ) : viewMode === 'grid' ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                        {filteredDocuments.map((doc) => {
                            const { icon: Icon, color, bg } = getFileIcon(doc.doc_type)
                            return (
                                <DocumentCard
                                    key={doc.id}
                                    doc={doc}
                                    Icon={Icon}
                                    color={color}
                                    bg={bg}
                                    onDelete={handleDeleteDocument}
                                    isDeleting={deletingId === doc.document_id}
                                    getFileName={getFileName}
                                />
                            )
                        })}
                    </div>
                ) : (
                    <div className="space-y-2">
                        {filteredDocuments.map((doc) => {
                            const { icon: Icon, color, bg } = getFileIcon(doc.doc_type)
                            return (
                                <DocumentRow
                                    key={doc.id}
                                    doc={doc}
                                    Icon={Icon}
                                    color={color}
                                    bg={bg}
                                    formatDate={formatDate}
                                    onDelete={handleDeleteDocument}
                                    isDeleting={deletingId === doc.document_id}
                                    getFileName={getFileName}
                                />
                            )
                        })}
                    </div>
                )}
            </div>
        </main>
    )
}

function DocumentCard({ doc, Icon, color, bg, onDelete, isDeleting, getFileName }) {
    const fileName = getFileName(doc.name)

    return (
        <div className="card p-4 hover:border-aegis-rag-accent/30 transition-fast group cursor-pointer relative">
            <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center mb-4`}>
                <Icon size={24} className={color} />
            </div>
            <h3 className="font-medium text-aegis-rag-text-primary truncate mb-1 group-hover:text-aegis-rag-accent transition-fast">
                {fileName}
            </h3>
            <p className="text-xs text-aegis-rag-text-muted">
                {doc.chunks || 0} chunks • {doc.doc_type || 'unknown'}
            </p>
            <button
                onClick={(e) => {
                    e.stopPropagation()
                    onDelete(doc.document_id)
                }}
                disabled={isDeleting}
                className="absolute top-3 right-3 p-2 rounded-lg bg-aegis-rag-bg-elevated opacity-0 group-hover:opacity-100 hover:bg-aegis-rag-error/20 hover:text-aegis-rag-error transition-fast"
            >
                {isDeleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
            </button>
        </div>
    )
}

function DocumentRow({ doc, Icon, color, bg, formatDate, onDelete, isDeleting, getFileName }) {
    const fileName = getFileName(doc.name)

    return (
        <div className="flex items-center gap-4 p-4 bg-aegis-rag-bg-card border border-aegis-rag-border rounded-xl hover:border-aegis-rag-accent/30 transition-fast group">
            <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center flex-shrink-0`}>
                <Icon size={20} className={color} />
            </div>
            <div className="flex-1 min-w-0">
                <h3 className="font-medium text-aegis-rag-text-primary truncate group-hover:text-aegis-rag-accent transition-fast">
                    {fileName}
                </h3>
                <p className="text-xs text-aegis-rag-text-muted">
                    {doc.chunks || 0} chunks • {doc.doc_type || 'unknown'} • {formatDate(doc.created_at)}
                </p>
            </div>
            <div className="flex items-center gap-1">
                <button className="btn-icon">
                    <Eye size={16} />
                </button>
                <button
                    onClick={() => onDelete(doc.document_id)}
                    disabled={isDeleting}
                    className="btn-icon hover:text-aegis-rag-error"
                >
                    {isDeleting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                </button>
            </div>
        </div>
    )
}

function EmptyLibrary({ onUpload, hasDocuments }) {
    return (
        <div className="h-full flex flex-col items-center justify-center">
            <div className="w-20 h-20 rounded-3xl bg-aegis-rag-bg-card border border-aegis-rag-border flex items-center justify-center mb-6">
                <FolderOpen size={36} className="text-aegis-rag-text-muted" />
            </div>
            <h2 className="text-xl font-semibold text-aegis-rag-text-primary mb-2">
                {hasDocuments ? 'No matching documents' : 'No documents yet'}
            </h2>
            <p className="text-aegis-rag-text-secondary text-center max-w-md mb-6">
                {hasDocuments
                    ? 'Try adjusting your search.'
                    : 'Upload documents to build your workspace. Aegis RAG supports PDFs, Word documents, images, and audio files.'
                }
            </p>
            <button onClick={onUpload} className="btn-primary flex items-center gap-2">
                <Plus size={18} />
                <span>Add Documents</span>
            </button>
        </div>
    )
}
