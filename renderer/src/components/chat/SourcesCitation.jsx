import { useState } from 'react'
import { ChevronDown, ChevronUp, FileText, ExternalLink } from 'lucide-react'
import { formatMatchScore } from '../../utils/score'

/**
 * SourcesCitation - Expandable sources component for AI messages
 * Shows filenames, page numbers, timestamps, and relevance scores
 */
export default function SourcesCitation({ sources, onSourceClick }) {
    const [isExpanded, setIsExpanded] = useState(false)

    if (!sources || sources.length === 0) return null

    return (
        <div className="mt-3">
            {/* Toggle Button */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm text-aegis-rag-text-secondary hover:text-aegis-rag-text-primary bg-aegis-rag-bg-elevated hover:bg-aegis-rag-bg-hover rounded-xl transition-fast"
            >
                <FileText size={16} className="text-aegis-rag-accent" />
                <span className="font-medium">
                    {sources.length} Source{sources.length > 1 ? 's' : ''}
                </span>
                {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {/* Expanded Sources List */}
            {isExpanded && (
                <div className="mt-3 space-y-2 animate-fade-in">
                    {sources.map((source, index) => (
                        <SourceCard
                            key={index}
                            source={source}
                            index={index + 1}
                            onClick={() => onSourceClick?.(source)}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

/**
 * Individual source card
 */
function SourceCard({ source, index, onClick }) {
    const getFileIcon = (filename) => {
        const ext = filename?.split('.').pop()?.toLowerCase()
        switch (ext) {
            case 'pdf': return '📄'
            case 'docx':
            case 'doc': return '📝'
            case 'png':
            case 'jpg':
            case 'jpeg': return '🖼️'
            case 'mp3':
            case 'wav': return '🎵'
            default: return '📎'
        }
    }

    const filename = source.filename || source.file_name || source.document_name || 'Unknown Source'
    const page = source.page || source.page_number
    const timestamp = source.timestamp
    const score = source.score || source.relevance_score
    const matchScore = formatMatchScore(score)

    return (
        <button
            onClick={onClick}
            className="w-full flex items-center gap-4 p-4 rounded-2xl bg-aegis-rag-bg-card border border-aegis-rag-border hover:border-aegis-rag-accent/30 hover:bg-aegis-rag-bg-elevated transition-fast group text-left"
        >
            {/* Index Badge */}
            <div className="w-8 h-8 rounded-lg bg-aegis-rag-accent/20 flex items-center justify-center flex-shrink-0">
                <span className="text-aegis-rag-accent font-semibold text-sm">{index}</span>
            </div>

            {/* File Icon */}
            <div className="w-10 h-10 rounded-xl bg-aegis-rag-bg-elevated flex items-center justify-center flex-shrink-0 text-xl">
                {getFileIcon(filename)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <p className="font-medium text-aegis-rag-text-primary truncate group-hover:text-aegis-rag-accent transition-fast">
                    {filename}
                </p>
                <div className="flex items-center gap-3 mt-1 text-xs text-aegis-rag-text-muted">
                    {page && <span>Page {page}</span>}
                    {timestamp && <span>@ {timestamp}</span>}
                    {matchScore && (
                        <span className="badge badge-accent">
                            {matchScore}
                        </span>
                    )}
                </div>
                {source.snippet && (
                    <p className="text-sm text-aegis-rag-text-secondary mt-2 line-clamp-2">
                        "{source.snippet}"
                    </p>
                )}
            </div>

            {/* External Link Icon */}
            <ExternalLink
                size={16}
                className="text-aegis-rag-text-muted group-hover:text-aegis-rag-accent transition-fast flex-shrink-0"
            />
        </button>
    )
}
