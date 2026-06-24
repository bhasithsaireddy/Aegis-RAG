import { FileText, Image, Mic, File, X, Check, Loader2, AlertCircle } from 'lucide-react'
import useStore from '../../store/store'

/**
 * FileQueue - List of queued files for ingestion
 * Shows file name, size, type icon, and status
 */
export default function FileQueue() {
    const { ingestionQueue, removeFromIngestionQueue } = useStore()

    if (ingestionQueue.length === 0) {
        return null
    }

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    const getFileIcon = (fileName, mimeType) => {
        const ext = fileName.split('.').pop()?.toLowerCase()

        if (ext === 'pdf') return { icon: FileText, color: 'text-red-400', bg: 'bg-red-400/10' }
        if (['docx', 'doc'].includes(ext)) return { icon: FileText, color: 'text-blue-400', bg: 'bg-blue-400/10' }
        if (['png', 'jpg', 'jpeg'].includes(ext)) return { icon: Image, color: 'text-aegis-rag-text-secondary', bg: 'bg-aegis-rag-bg-elevated' }
        if (['wav', 'mp3'].includes(ext)) return { icon: Mic, color: 'text-purple-400', bg: 'bg-purple-400/10' }
        return { icon: File, color: 'text-aegis-rag-text-muted', bg: 'bg-aegis-rag-bg-elevated' }
    }

    const getStatusIcon = (status) => {
        switch (status) {
            case 'processing':
                return <Loader2 size={16} className="text-aegis-rag-warning animate-spin" />
            case 'done':
                return <Check size={16} className="text-aegis-rag-success" />
            case 'error':
                return <AlertCircle size={16} className="text-aegis-rag-error" />
            default:
                return null
        }
    }

    return (
        <div className="space-y-2">
            <h4 className="text-sm font-medium text-aegis-rag-text-muted mb-3">
                {ingestionQueue.length} file{ingestionQueue.length > 1 ? 's' : ''} queued
            </h4>

            <div className="space-y-2 max-h-[240px] overflow-y-auto scrollbar-thin pr-2">
                {ingestionQueue.map((item) => {
                    const { icon: Icon, color, bg } = getFileIcon(item.name, item.type)

                    return (
                        <div
                            key={item.id}
                            className={`flex items-center gap-3 p-3 rounded-xl border transition-fast ${item.status === 'error'
                                    ? 'bg-aegis-rag-error/5 border-aegis-rag-error/20'
                                    : item.status === 'done'
                                        ? 'bg-aegis-rag-success/5 border-aegis-rag-success/20'
                                        : 'bg-aegis-rag-bg-card border-aegis-rag-border hover:border-aegis-rag-border-light'
                                }`}
                        >
                            {/* File Icon */}
                            <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center flex-shrink-0`}>
                                <Icon size={20} className={color} />
                            </div>

                            {/* File Info */}
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-aegis-rag-text-primary truncate">
                                    {item.name}
                                </p>
                                <p className="text-xs text-aegis-rag-text-muted">
                                    {formatFileSize(item.size)}
                                </p>
                            </div>

                            {/* Status or Remove */}
                            <div className="flex items-center gap-2">
                                {getStatusIcon(item.status)}

                                {item.status === 'queued' && (
                                    <button
                                        onClick={() => removeFromIngestionQueue(item.id)}
                                        className="p-1.5 text-aegis-rag-text-muted hover:text-aegis-rag-error rounded-lg hover:bg-aegis-rag-error/10 transition-fast"
                                        title="Remove file"
                                    >
                                        <X size={16} />
                                    </button>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
