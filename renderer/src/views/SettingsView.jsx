import { useState, useEffect } from 'react'
import { Settings, Server, CheckCircle, XCircle, Loader2, Save, Cpu, Mic } from 'lucide-react'
import useStore from '../store/store'
import api from '../services/api'

/**
 * SettingsView - Runtime configuration that actually affects the backend
 */
export default function SettingsView() {
    const { backendStatus, systemInfo } = useStore()

    const [backendSettings, setBackendSettings] = useState(null)
    const [isSaving, setIsSaving] = useState(false)
    const [saveMessage, setSaveMessage] = useState(null)

    // Load backend settings on mount
    useEffect(() => {
        if (backendStatus !== 'connected') return
        api.getSettings()
            .then(s => setBackendSettings(s))
            .catch(err => console.warn('Could not load settings:', err.message))
    }, [backendStatus])

    const handleSave = async () => {
        if (!backendSettings) return
        setIsSaving(true)
        setSaveMessage(null)
        try {
            const updated = await api.updateSettings({
                ollama_host: backendSettings.ollama_host,
                llm_model: backendSettings.llm_model,
                vision_model: backendSettings.vision_model,
                whisper_model: backendSettings.whisper_model,
                chunk_size: backendSettings.chunk_size,
                top_k_results: backendSettings.top_k_results,
                use_reranker: backendSettings.use_reranker,
                use_hybrid_search: backendSettings.use_hybrid_search,
            })
            setBackendSettings(updated)
            setSaveMessage({ type: 'success', text: 'Settings saved successfully.' })
        } catch (err) {
            setSaveMessage({ type: 'error', text: `Save failed: ${err.message}` })
        } finally {
            setIsSaving(false)
            setTimeout(() => setSaveMessage(null), 3000)
        }
    }

    const patch = (key, value) => setBackendSettings(prev => ({ ...prev, [key]: value }))

    return (
        <main className="flex-1 flex flex-col bg-aegis-rag-bg-app overflow-hidden">
            <div className="px-6 py-4 border-b border-aegis-rag-border flex-shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Settings size={24} className="text-aegis-rag-text-secondary" />
                        <div>
                            <h1 className="text-xl font-semibold text-aegis-rag-text-primary">Settings</h1>
                            <p className="text-sm text-aegis-rag-text-muted">Configure Aegis RAG to your preferences</p>
                        </div>
                    </div>
                    {backendSettings && (
                        <button
                            onClick={handleSave}
                            disabled={isSaving}
                            className="btn-primary flex items-center gap-2"
                        >
                            {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                            {isSaving ? 'Saving…' : 'Save Changes'}
                        </button>
                    )}
                </div>
                {saveMessage && (
                    <p className={`mt-2 text-sm ${saveMessage.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                        {saveMessage.text}
                    </p>
                )}
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
                <div className="max-w-2xl space-y-6">

                    {/* ── Runtime Status ── */}
                    <section className="card p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <Server size={20} className="text-aegis-rag-text-secondary" />
                            <h2 className="font-semibold text-aegis-rag-text-primary">Runtime Status</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {[
                                { label: 'Backend', available: backendStatus === 'connected', model: 'FastAPI' },
                                { label: 'LLM', available: systemInfo.llmAvailable, model: systemInfo.llmModel },
                                { label: 'Vision', available: systemInfo.visionAvailable, model: systemInfo.visionModel },
                            ].map(({ label, available, model }) => (
                                <div key={label} className="p-4 bg-aegis-rag-bg-elevated rounded-xl border border-aegis-rag-border">
                                    <p className="text-xs uppercase tracking-wider text-aegis-rag-text-muted mb-2">{label}</p>
                                    <div className="flex items-center gap-2 mb-1">
                                        {available
                                            ? <CheckCircle size={14} className="text-green-400" />
                                            : <XCircle size={14} className="text-red-400" />
                                        }
                                        <span className="text-sm text-aegis-rag-text-primary">
                                            {available ? 'Available' : 'Unavailable'}
                                        </span>
                                    </div>
                                    <p className="text-xs text-aegis-rag-text-muted truncate">{model}</p>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* ── Ollama Connection ── */}
                    {backendSettings?.deployment_mode !== 'cloud' && (
                    <div className="bg-aegis-rag-bg-tertiary border border-aegis-rag-border rounded-xl p-6">
                        <div className="flex items-center gap-3 mb-4">
                            <Server size={20} className="text-aegis-rag-text-secondary" />
                            <h2 className="text-lg font-medium text-aegis-rag-text-primary">Ollama Connection</h2>
                        </div>
                        
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-aegis-rag-text-secondary mb-1">
                                    Ollama Host URL
                                </label>
                                <input
                                    type="text"
                                    value={backendSettings?.ollama_host ?? ''}
                                    onChange={e => patch('ollama_host', e.target.value)}
                                    placeholder="http://localhost:11434"
                                    disabled={!backendSettings}
                                    className="w-full bg-aegis-rag-bg-primary border border-aegis-rag-border rounded-lg px-4 py-2.5 text-aegis-rag-text-primary focus:outline-none focus:border-aegis-rag-accent focus:ring-1 focus:ring-aegis-rag-accent/50 transition-all disabled:opacity-50"
                                />
                                <p className="text-xs text-aegis-rag-text-secondary mt-1">URL where your local Ollama instance is running</p>
                            </div>
                        </div>
                    </div>
                    )}

                    {/* ── Models ── */}
                    <section className="card p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <Cpu size={20} className="text-aegis-rag-text-secondary" />
                            <h2 className="font-semibold text-aegis-rag-text-primary">Models</h2>
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-aegis-rag-text-secondary mb-1">
                                        LLM Model
                                    </label>
                                    <input
                                        type="text"
                                        value={backendSettings?.llm_model ?? ''}
                                        onChange={e => patch('llm_model', e.target.value)}
                                        placeholder="mistral:7b"
                                        className="input"
                                        disabled={!backendSettings}
                                    />
                                </div>
                                {backendSettings?.deployment_mode !== 'cloud' && (
                                <div>
                                    <label className="block text-sm font-medium text-aegis-rag-text-secondary mb-1">
                                        Vision Model
                                    </label>
                                    <input
                                        type="text"
                                        value={backendSettings?.vision_model ?? ''}
                                        onChange={e => patch('vision_model', e.target.value)}
                                        placeholder="llava"
                                        disabled={!backendSettings}
                                        className="w-full bg-aegis-rag-bg-primary border border-aegis-rag-border rounded-lg px-4 py-2.5 text-aegis-rag-text-primary focus:outline-none focus:border-aegis-rag-accent focus:ring-1 focus:ring-aegis-rag-accent/50 transition-all disabled:opacity-50"
                                    />
                                    <p className="text-xs text-aegis-rag-text-secondary mt-1">Model used for Image OCR</p>
                                </div>
                                )}
                            </div>
                        </div>
                    </section>

                    {/* ── Voice Settings ── */}
                    <section className="card p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <Mic size={20} className="text-aegis-rag-text-secondary" />
                            <h2 className="font-semibold text-aegis-rag-text-primary">Voice & Transcription</h2>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-aegis-rag-text-secondary mb-1">
                                Whisper Model Size
                            </label>
                            <select
                                value={backendSettings?.whisper_model ?? 'base'}
                                onChange={e => patch('whisper_model', e.target.value)}
                                className="input"
                                disabled={!backendSettings}
                            >
                                {['tiny', 'base', 'small', 'medium', 'large-v2'].map(m => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                            <p className="text-xs text-aegis-rag-text-muted mt-1">
                                Larger models are more accurate but slower and use more RAM.
                            </p>
                        </div>
                    </section>

                    {/* ── Retrieval Settings ── */}
                    <section className="card p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <Server size={20} className="text-aegis-rag-text-secondary" />
                            <h2 className="font-semibold text-aegis-rag-text-primary">Retrieval</h2>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-aegis-rag-text-secondary mb-1">
                                    Top-K Results
                                </label>
                                <input
                                    type="number"
                                    min={1} max={20}
                                    value={backendSettings?.top_k_results ?? 5}
                                    onChange={e => patch('top_k_results', parseInt(e.target.value))}
                                    className="input w-32"
                                    disabled={!backendSettings}
                                />
                            </div>
                            <div className="flex items-center gap-3">
                                <input
                                    type="checkbox"
                                    id="use-reranker"
                                    checked={backendSettings?.use_reranker ?? true}
                                    onChange={e => patch('use_reranker', e.target.checked)}
                                    disabled={!backendSettings}
                                    className="w-4 h-4"
                                />
                                <label htmlFor="use-reranker" className="text-sm text-aegis-rag-text-primary">
                                    Enable Cross-Encoder Reranker
                                </label>
                            </div>
                            <div className="flex items-center gap-3">
                                <input
                                    type="checkbox"
                                    id="use-hybrid"
                                    checked={backendSettings?.use_hybrid_search ?? false}
                                    onChange={e => patch('use_hybrid_search', e.target.checked)}
                                    disabled={!backendSettings}
                                    className="w-4 h-4"
                                />
                                <label htmlFor="use-hybrid" className="text-sm text-aegis-rag-text-primary">
                                    Enable Hybrid Search (BM25 + Dense)
                                </label>
                            </div>
                        </div>
                    </section>

                    {/* ── About ── */}
                    <section className="card p-6">
                        <h2 className="font-semibold text-aegis-rag-text-primary mb-4">About Aegis RAG</h2>
                        <div className="space-y-2 text-sm text-aegis-rag-text-secondary">
                            <p>Version: 1.0.0</p>
                            <p>Offline multimodal RAG workspace</p>
                            <p className="text-aegis-rag-text-muted">
                                Built with Electron, React, and FastAPI. All processing happens locally.
                            </p>
                        </div>
                    </section>

                </div>
            </div>
        </main>
    )
}
