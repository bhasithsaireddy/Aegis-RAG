import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Mic, Loader2 } from 'lucide-react'

/**
 * ChatInput - Fixed input area for composing messages
 * Features large textarea, send button, and file attachment indicators
 */
export default function ChatInput({ onSend, isLoading = false, disabled = false }) {
    const [message, setMessage] = useState('')
    const textareaRef = useRef(null)

    // Auto-resize textarea
    useEffect(() => {
        const textarea = textareaRef.current
        if (textarea) {
            textarea.style.height = 'auto'
            textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
        }
    }, [message])

    const handleSubmit = (e) => {
        e.preventDefault()
        if (message.trim() && !isLoading && !disabled) {
            onSend(message.trim())
            setMessage('')
            // Reset textarea height
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto'
            }
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit(e)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="p-4 border-t border-aegis-rag-border bg-aegis-rag-bg-app">
            <div className="max-w-4xl mx-auto">
                <div className="relative flex items-center gap-3 bg-aegis-rag-bg-card border border-aegis-rag-border rounded-3xl px-4 py-3 focus-within:border-aegis-rag-accent/50 transition-fast">
                    {/* Attachment Button
                    <button
                        type="button"
                        className="p-2 text-aegis-rag-text-muted hover:text-aegis-rag-text-primary rounded-xl hover:bg-aegis-rag-bg-hover transition-fast flex-shrink-0"
                        title="Attach file"
                    >
                        <Paperclip size={20} />
                    </button> */}

                    {/* Textarea */}
                    <textarea
                        ref={textareaRef}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask anything about your documents..."
                        disabled={disabled}
                        rows={1}
                        className="flex-1 bg-transparent text-aegis-rag-text-primary placeholder:text-aegis-rag-text-muted text-base resize-none outline-none min-h-[28px] max-h-[200px] py-1"
                    />

                    {/* Voice Button
                    <button
                        type="button"
                        className="p-2 text-aegis-rag-text-muted hover:text-aegis-rag-text-primary rounded-xl hover:bg-aegis-rag-bg-hover transition-fast flex-shrink-0"
                        title="Voice input"
                    >
                        <Mic size={20} />
                    </button> */}

                    {/* Send Button */}
                    <button
                        type="submit"
                        disabled={!message.trim() || isLoading || disabled}
                        className={`p-3 rounded-xl transition-fast flex-shrink-0 flex items-center justify-center ${message.trim() && !isLoading && !disabled
                            ? 'bg-aegis-rag-accent text-aegis-rag-bg-app hover:bg-aegis-rag-accent-light shadow-lg shadow-aegis-rag-accent/20'
                            : 'bg-aegis-rag-bg-elevated text-aegis-rag-text-muted cursor-not-allowed'
                            }`}
                    >
                        {isLoading ? (
                            <Loader2 size={20} className="animate-spin" />
                        ) : (
                            <Send size={20} />
                        )}
                    </button>
                </div>

                {/* Helper Text */}
                <p className="text-xs text-aegis-rag-text-muted text-center mt-3">
                    Press <kbd className="px-1.5 py-0.5 bg-aegis-rag-bg-card rounded text-aegis-rag-text-secondary">Enter</kbd> to send,
                    <kbd className="px-1.5 py-0.5 bg-aegis-rag-bg-card rounded text-aegis-rag-text-secondary ml-1">Shift+Enter</kbd> for new line
                </p>
            </div>
        </form>
    )
}
