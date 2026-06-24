/**
 * Aegis RAG API Client
 * Handles all communication with the Python FastAPI backend
 */

class ApiClient {
    constructor() {
        const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        this.baseUrl = import.meta.env?.VITE_API_BASE_URL || (isLocalhost ? 'http://127.0.0.1:8000' : window.location.origin);
    }

    /**
     * Set the base URL dynamically (useful for runtime port configuration)
     */
    setBaseUrl(url) {
        this.baseUrl = url
    }

    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
            }

            // Handle empty responses
            const text = await response.text()
            return text ? JSON.parse(text) : null
        } catch (error) {
            // Handle network errors gracefully (backend not started yet)
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Backend not available. Please wait for the server to start.')
            }
            throw error
        }
    }

    // ============================================
    // Health & Status Endpoints
    // ============================================

    /**
     * Check if backend is healthy
     */
    async checkHealth() {
        try {
            await this.request('/health')
            return true
        } catch {
            return false
        }
    }

    /**
     * Get system statistics
     */
    async getStats() {
        return this.request('/api/stats')
    }

    /**
     * Get model status (LLM availability)
     */
    async getModelStatus() {
        return this.request('/api/models/status')
    }

    /**
     * Get supported file types for ingestion
     */
    async getSupportedTypes() {
        return this.request('/api/ingest/supported')
    }

    // ============================================
    // Query Endpoints
    // ============================================

    /**
     * Send a query and get a response (non-streaming)
     */
    async query(queryText, options = {}) {
        return this.request('/api/query', {
            method: 'POST',
            body: JSON.stringify({
                query: queryText,
                top_k: options.topK || 5,
                doc_types: options.docTypes || null,
                collections: options.collections || null,
                session_id: options.sessionId || null,
            }),
        })
    }

    /**
     * Send a query with streaming response
     * Returns an async generator that yields parsed NDJSON objects
     */
    async *queryStream(queryText, options = {}) {
        const url = `${this.baseUrl}/api/query/stream`

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: queryText,
                top_k: options.topK || 5,
                doc_types: options.docTypes || null,
                collections: options.collections || null,
                session_id: options.sessionId || null,
            }),
        })

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        try {
            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')

                // Keep the last incomplete line in the buffer
                buffer = lines.pop() || ''

                for (const line of lines) {
                    if (!line.trim()) continue

                    try {
                        const parsed = JSON.parse(line)

                        // Handle different message types from backend
                        if (parsed.type === 'chunk') {
                            yield { type: 'token', content: parsed.content }
                        } else if (parsed.type === 'answer') {
                            // Full answer for empty results
                            yield { type: 'token', content: parsed.content }
                        } else if (parsed.type === 'sources') {
                            yield { type: 'sources', content: parsed.sources }
                        } else if (parsed.type === 'error') {
                            throw new Error(parsed.error)
                        } else if (parsed.type === 'done') {
                            return
                        }
                    } catch (parseError) {
                        // If JSON parsing fails, treat as raw content
                        if (parseError instanceof SyntaxError) {
                            yield { type: 'token', content: line }
                        } else {
                            throw parseError
                        }
                    }
                }
            }

            // Process any remaining content in buffer
            if (buffer.trim()) {
                try {
                    const parsed = JSON.parse(buffer)
                    if (parsed.type === 'chunk') {
                        yield { type: 'token', content: parsed.content }
                    } else if (parsed.type === 'sources') {
                        yield { type: 'sources', content: parsed.sources }
                    }
                } catch {
                    // Ignore incomplete JSON at the end
                }
            }
        } finally {
            reader.releaseLock()
        }
    }

    /**
     * Perform semantic search without LLM generation
     */
    async search(queryText, options = {}) {
        return this.request('/api/search', {
            method: 'POST',
            body: JSON.stringify({
                query: queryText,
                top_k: options.topK || 10,
                doc_types: options.docTypes || null,
                collections: options.collections || null,
            }),
        })
    }

    // ============================================
    // Collection Endpoints
    // ============================================

    /**
     * Get all collections
     */
    async getCollections() {
        return this.request('/api/collections')
    }

    /**
     * Create a new collection
     */
    async createCollection(name) {
        return this.request(`/api/collections?name=${encodeURIComponent(name)}`, {
            method: 'POST',
        })
    }

    /**
     * Delete a collection
     */
    async deleteCollection(name) {
        return this.request(`/api/collections/${encodeURIComponent(name)}`, {
            method: 'DELETE',
        })
    }

    /**
     * Add a document to a collection
     */
    async addDocumentToCollection(documentId, collection) {
        return this.request('/api/collections/add', {
            method: 'POST',
            body: JSON.stringify({
                document_id: documentId,
                collection: collection,
            }),
        })
    }

    /**
     * Get documents in a specific collection
     */
    async getCollectionDocuments(collection) {
        return this.request(`/api/collections/${encodeURIComponent(collection)}/documents`)
    }

    // ============================================
    // Document Endpoints
    // ============================================

    /**
     * Get all documents
     */
    async getDocuments() {
        return this.request('/api/documents')
    }

    /**
     * Delete a document
     */
    async deleteDocument(documentId) {
        return this.request(`/api/documents/${encodeURIComponent(documentId)}`, {
            method: 'DELETE',
        })
    }

    // ============================================
    // Ingestion Endpoints
    // ============================================

    /**
     * Ingest a single file
     */
    async ingestFile(file, collections = null) {
        const formData = new FormData()
        formData.append('file', file)

        if (collections && collections.length > 0) {
            formData.append('collections', collections.join(','))
        }

        const response = await fetch(`${this.baseUrl}/api/ingest`, {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `HTTP ${response.status}`)
        }

        return response.json()
    }

    /**
     * Ingest multiple files in batch
     */
    async ingestFiles(files, collections = null) {
        const formData = new FormData()

        for (const file of files) {
            formData.append('files', file)
        }

        if (collections && collections.length > 0) {
            formData.append('collections', collections.join(','))
        }

        const response = await fetch(`${this.baseUrl}/api/ingest/batch`, {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `HTTP ${response.status}`)
        }

        return response.json()
    }

    // ============================================
    // Voice/Diarization Endpoints
    // ============================================

    /**
     * Get diarization service status
     */
    async getDiarizationStatus() {
        return this.request('/api/voice/diarize/status')
    }

    /**
     * Transcribe audio file (without speaker diarization)
     */
    async transcribeAudio(file, language = null) {
        const formData = new FormData()
        formData.append('file', file)

        if (language) {
            formData.append('language', language)
        }

        const response = await fetch(`${this.baseUrl}/api/voice/transcribe/upload`, {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `HTTP ${response.status}`)
        }

        return response.json()
    }

    /**
     * Diarize audio file (with speaker identification)
     */
    async diarizeAudio(file, options = {}) {
        const formData = new FormData()
        formData.append('file', file)

        if (options.language) {
            formData.append('language', options.language)
        }
        if (options.numSpeakers) {
            formData.append('num_speakers', options.numSpeakers.toString())
        }

        const response = await fetch(`${this.baseUrl}/api/voice/diarize/upload`, {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `HTTP ${response.status}`)
        }

        return response.json()
    }
    // ============================================
    // Chat History Endpoints
    // ============================================

    /**
     * Get recent chat sessions
     */
    async getSessions(limit = 50) {
        return this.request(`/api/chat/sessions?limit=${limit}`)
    }

    /**
     * Create a new chat session
     */
    async createSession(title = "New Chat") {
        return this.request('/api/chat/sessions', {
            method: 'POST',
            body: JSON.stringify({ title }),
        })
    }

    /**
     * Get messages for a session
     */
    async getSessionMessages(sessionId) {
        return this.request(`/api/chat/sessions/${sessionId}/messages`)
    }

    /**
     * Delete a chat session
     */
    async deleteSession(sessionId) {
        return this.request(`/api/chat/sessions/${sessionId}`, {
            method: 'DELETE',
        })
    }

    /**
     * Update session title
     */
    async updateSession(sessionId, title) {
        return this.request(`/api/chat/sessions/${sessionId}`, {
            method: 'PATCH',
            body: JSON.stringify({ title }),
        })
    }

    // ============================================
    // Settings Endpoints
    // ============================================

    /**
     * Get current backend settings
     */
    async getSettings() {
        return this.request('/api/settings')
    }

    /**
     * Update backend settings at runtime
     */
    async updateSettings(settings) {
        return this.request('/api/settings', {
            method: 'PATCH',
            body: JSON.stringify(settings),
        })
    }

}

// Create and export singleton instance
const api = new ApiClient()
export default api

// Also export the class for testing/custom instances
export { ApiClient }
