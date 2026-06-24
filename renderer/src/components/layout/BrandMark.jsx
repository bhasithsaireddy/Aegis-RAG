export default function BrandMark({ compact = false, className = '' }) {
    return (
        <div className={`flex items-center gap-3 ${className}`}>
            <div className={`relative overflow-hidden rounded-2xl border border-aegis-rag-border bg-aegis-rag-bg-card ${compact ? 'w-10 h-10' : 'w-12 h-12'}`}>
                <svg viewBox="0 0 64 64" className="absolute inset-0 h-full w-full" aria-hidden="true">
                    <defs>
                        <linearGradient id="core-glow" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#ffffff" />
                            <stop offset="100%" stopColor="#a0a0a0" />
                        </linearGradient>
                        <linearGradient id="ring-glow" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="rgba(255,255,255,0.8)" />
                            <stop offset="100%" stopColor="rgba(255,255,255,0.1)" />
                        </linearGradient>
                    </defs>

                    <rect width="64" height="64" fill="#0a0a0a" />

                    <circle cx="32" cy="32" r="24" fill="none" stroke="url(#ring-glow)" strokeWidth="1" opacity="0.3" strokeDasharray="4 2" />
                    <circle cx="32" cy="32" r="18" fill="none" stroke="url(#ring-glow)" strokeWidth="1.5" opacity="0.6" />
                    <circle cx="32" cy="32" r="12" fill="none" stroke="url(#ring-glow)" strokeWidth="2" opacity="0.8" strokeDasharray="8 4" />
                    
                    <circle cx="32" cy="32" r="6" fill="url(#core-glow)" />
                    <circle cx="32" cy="32" r="2" fill="#ffffff" />
                    
                    <path d="M32 8 L32 14 M32 50 L32 56 M8 32 L14 32 M50 32 L56 32" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M15 15 L19.2 19.2 M49 49 L44.8 44.8 M15 49 L19.2 44.8 M49 15 L44.8 19.2" stroke="rgba(255,255,255,0.3)" strokeWidth="1" strokeLinecap="round" />
                </svg>
            </div>
            <div className="leading-tight">
                <p className="text-sm font-semibold tracking-[0.28em] text-aegis-rag-text-primary uppercase">Aegis RAG</p>
                {!compact && <p className="text-xs text-aegis-rag-text-muted">Monochrome workspace</p>}
            </div>
        </div>
    )
}