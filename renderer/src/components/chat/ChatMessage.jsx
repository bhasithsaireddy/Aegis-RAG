import { useState } from 'react'
import { User, Bot, ChevronDown, ChevronUp, FileText, Clock } from 'lucide-react'
import { formatMatchScore } from '../../utils/score'

/**
 * ChatMessage - Individual message bubble component
 * Handles both user and AI messages with citation support
 */
export default function ChatMessage({ message }) {
    const [showSources, setShowSources] = useState(false)
    const isUser = message.role === 'user'
    const hasSources = message.sources && message.sources.length > 0

    const formatTime = (date) => {
        return new Date(date).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    return (
        <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} animate-in`}>
            {/* AI Avatar */}
            {!isUser && (
                <div className="w-9 h-9 rounded-xl bg-aegis-rag-bg-card border border-aegis-rag-border flex items-center justify-center flex-shrink-0">
                    <Bot size={18} className="text-aegis-rag-accent" />
                </div>
            )}

            {/* Message Content */}
            <div className={`max-w-[75%] ${isUser ? 'order-first' : ''}`}>
                <div
                    className={`px-5 py-3.5 ${isUser
                        ? 'message-user'
                        : message.isError
                            ? 'bg-aegis-rag-error/20 text-aegis-rag-error rounded-3xl rounded-bl-lg'
                            : 'message-ai'
                        }`}
                >
                    <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
                        {message.content}
                    </p>
                </div>

                {/* Timestamp and Collection Scope */}
                <div className={`flex flex-wrap items-center gap-2 mt-1.5 px-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <Clock size={12} className="text-aegis-rag-text-muted" />
                    <span className="text-xs text-aegis-rag-text-muted">
                        {formatTime(message.timestamp)}
                    </span>
                    {/* Show collection filter for user messages */}
                    {isUser && message.collections && message.collections.length > 0 && (
                        <span className="text-xs text-aegis-rag-accent bg-aegis-rag-accent/10 px-2 py-0.5 rounded-full">
                            🔍 in {message.collections.join(', ')}
                        </span>
                    )}
                </div>

                {/* Sources Toggle (AI messages only) */}
                {!isUser && hasSources && (
                    <div className="mt-2">
                        <button
                            onClick={() => setShowSources(!showSources)}
                            className="flex items-center gap-2 px-3 py-1.5 text-xs text-aegis-rag-text-muted hover:text-aegis-rag-text-secondary transition-fast rounded-lg hover:bg-aegis-rag-bg-hover"
                        >
                            <FileText size={14} />
                            <span>{message.sources.length} Source{message.sources.length > 1 ? 's' : ''}</span>
                            {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>

                        {/* Expanded Sources */}
                        {showSources && (
                            <div className="mt-2 ml-2 space-y-1.5">
                                {message.sources.map((source, index) => {
                                    // Get the full path for opening
                                    const fullPath = source.file_name || source.filename || ''
                                    // Extract just the filename for display
                                    const displayName = fullPath ? fullPath.replace(/\\/g, '/').split('/').pop() : 'Unknown Source'

                                    // Open file handler
                                    const handleOpenFile = () => {
                                        if (fullPath) {
                                            const fileUrl = `file:///${fullPath.replace(/\\/g, '/')}`
                                            window.open(fileUrl, '_blank')
                                        }
                                    }

                                    return (
                                        <button
                                            key={index}
                                            onClick={handleOpenFile}
                                            className="w-full text-left flex items-center gap-3 px-3 py-2 rounded-xl bg-aegis-rag-bg-elevated hover:bg-aegis-rag-bg-hover transition-fast group"
                                            title={`Open: ${fullPath}`}
                                        >
                                            <div className="w-7 h-7 rounded-lg bg-aegis-rag-bg-card flex items-center justify-center flex-shrink-0">
                                                <FileText size={14} className="text-aegis-rag-accent" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-aegis-rag-text-primary truncate font-medium">
                                                    {displayName}
                                                </p>
                                                <p className="text-xs text-aegis-rag-text-muted">
                                                    {source.page && `Page ${source.page}`}
                                                    {source.timestamp && `@ ${source.timestamp}`}
                                                    {formatMatchScore(source.score) && ` • ${formatMatchScore(source.score)}`}
                                                </p>
                                            </div>
                                        </button>
                                    )
                                })}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* User Avatar */}
            {isUser && (
                <div className="w-9 h-9 rounded-xl bg-aegis-rag-accent flex items-center justify-center flex-shrink-0">
                    <User size={18} className="text-aegis-rag-bg-app" />
                </div>
            )}
        </div>
    )
}
