import { useState, useCallback } from 'react'
import api from '../services/api'
import useStore from '../store/store'

/**
 * Custom hook for handling streaming responses from the backend
 * Manages token-by-token updates, citation handling, and collection filtering
 */
export default function useStreamingResponse() {
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState(null)
    const {
        addMessage,
        appendToLastMessage,
        setStreaming,
        setActiveSources,
        selectedCollections
    } = useStore()

    /**
     * Send a query and stream the response
     * Automatically uses selected collections from store if no options provided
     */
    const sendQuery = useCallback(async (query, options = {}) => {
        setIsLoading(true)
        setError(null)
        setStreaming(true)

        // Get current selected collections and chat ID from store
        const state = useStore.getState()
        const currentSelectedCollections = state.selectedCollections
        const currentChatId = state.currentChatId

        // Merge options with selected collections (options take precedence)
        const mergedOptions = {
            ...options,
            collections: options.collections || (currentSelectedCollections.length > 0 ? currentSelectedCollections : null),
            sessionId: options.sessionId || currentChatId,
        }

        // Add user message
        addMessage({
            role: 'user',
            content: query,
            // Show which collections the query is scoped to
            collections: mergedOptions.collections,
        })

        // Add empty AI message that we'll stream into
        addMessage({
            role: 'assistant',
            content: '',
            sources: [],
        })

        try {
            let sources = []

            // Stream tokens from the backend (NDJSON format)
            for await (const chunk of api.queryStream(query, mergedOptions)) {
                if (chunk.type === 'token') {
                    appendToLastMessage(chunk.content)
                } else if (chunk.type === 'sources') {
                    sources = chunk.content || []
                }
            }

            // Update the last message with sources if we got any
            if (sources.length > 0) {
                useStore.setState((state) => {
                    const messages = [...state.messages]
                    if (messages.length > 0) {
                        // Map backend source format to frontend format
                        messages[messages.length - 1].sources = sources.map((s, idx) => ({
                            index: s.index || idx + 1,
                            filename: s.file || s.filename || 'Unknown',
                            file_name: s.file || s.filename || 'Unknown',
                            type: s.type || 'document',
                            page: s.location?.includes('page') ? s.location.match(/\d+/)?.[0] : null,
                            timestamp: s.location?.includes('@') ? s.location : null,
                            score: s.similarity || 0,
                        }))
                    }
                    return { messages }
                })

                // Also set active sources for context panel
                setActiveSources(sources)
            }

        } catch (err) {
            setError(err.message)

            // Update the AI message with error
            useStore.setState((state) => {
                const messages = [...state.messages]
                if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
                    messages[messages.length - 1].content = `Error: ${err.message}`
                    messages[messages.length - 1].isError = true
                }
                return { messages }
            })
        } finally {
            setIsLoading(false)
            setStreaming(false)
        }
    }, [addMessage, appendToLastMessage, setStreaming, setActiveSources])

    /**
     * Send a query without streaming (for simpler responses)
     * Automatically uses selected collections from store if no options provided
     */
    const sendQuerySync = useCallback(async (query, options = {}) => {
        setIsLoading(true)
        setError(null)

        // Get current selected collections and chat ID from store
        const state = useStore.getState()
        const currentSelectedCollections = state.selectedCollections
        const currentChatId = state.currentChatId

        // Merge options with selected collections
        const mergedOptions = {
            ...options,
            collections: options.collections || (currentSelectedCollections.length > 0 ? currentSelectedCollections : null),
            sessionId: options.sessionId || currentChatId,
        }

        addMessage({
            role: 'user',
            content: query,
            collections: mergedOptions.collections,
        })

        try {
            const response = await api.query(query, mergedOptions)

            // Map backend response to frontend format
            const sources = (response.sources || []).map((s, idx) => ({
                index: s.index || idx + 1,
                filename: s.file || s.filename || 'Unknown',
                file_name: s.file || s.filename || 'Unknown',
                type: s.type || 'document',
                page: s.location?.includes('page') ? s.location.match(/\d+/)?.[0] : null,
                timestamp: s.location?.includes('@') ? s.location : null,
                score: s.similarity || 0,
            }))

            addMessage({
                role: 'assistant',
                content: response.answer || response.response || '',
                sources: sources,
                confidence: response.confidence,
            })

            // Set active sources for context panel
            if (sources.length > 0) {
                setActiveSources(response.sources)
            }

            return response
        } catch (err) {
            setError(err.message)
            addMessage({
                role: 'assistant',
                content: `Error: ${err.message}`,
                isError: true,
            })
            throw err
        } finally {
            setIsLoading(false)
        }
    }, [addMessage, setActiveSources])

    return {
        sendQuery,
        sendQuerySync,
        isLoading,
        error,
        clearError: () => setError(null),
    }
}
