import { Minus, Square, X } from 'lucide-react'
import useStore from '../../store/store'
import BrandMark from './BrandMark'

/**
 * TopBar - Slim status bar at the top of the application
 * Shows app title, backend status, and window controls
 */
export default function TopBar() {
    const { backendStatus, systemInfo } = useStore()

    const getStatusColor = () => {
        switch (backendStatus) {
            case 'connected': return 'status-dot-connected'
            case 'disconnected': return 'status-dot-disconnected'
            default: return 'status-dot-checking'
        }
    }

    const getStatusText = () => {
        switch (backendStatus) {
            case 'connected': return 'Connected'
            case 'disconnected': return 'Disconnected'
            default: return 'Connecting...'
        }
    }

    return (
        <header className="h-14 bg-aegis-rag-bg-panel border-b border-aegis-rag-border flex items-center justify-between px-4 drag-region backdrop-blur-xl">
            {/* Left: App Branding */}
            <div className="flex items-center gap-3 no-drag">
                <BrandMark compact />
            </div>

            {/* Center: System Stats */}
            <div className="flex items-center gap-6 text-xs text-aegis-rag-text-muted no-drag">
                <div className="flex items-center gap-2">
                    <span>Documents:</span>
                    <span className="text-aegis-rag-text-secondary font-medium">{systemInfo.totalDocuments}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span>Chunks:</span>
                    <span className="text-aegis-rag-text-secondary font-medium">{systemInfo.totalChunks}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span>LLM:</span>
                    <span className="text-aegis-rag-text-secondary font-medium">{systemInfo.llmModel}</span>
                </div>
            </div>

            {/* Right: Status & Window Controls */}
            <div className="flex items-center gap-4 no-drag">
                {/* Backend Status */}
                <div className="flex items-center gap-2 text-xs">
                    <div className={`status-dot ${getStatusColor()}`} />
                    <span className="text-aegis-rag-text-muted">{getStatusText()}</span>
                </div>

                {/* Window Controls (Electron) */}
                <div className="flex items-center gap-1">
                    <button className="btn-icon w-8 h-8 flex items-center justify-center hover:bg-aegis-rag-bg-hover">
                        <Minus size={14} />
                    </button>
                    <button className="btn-icon w-8 h-8 flex items-center justify-center hover:bg-aegis-rag-bg-hover">
                        <Square size={12} />
                    </button>
                    <button className="btn-icon w-8 h-8 flex items-center justify-center hover:bg-aegis-rag-error/20 hover:text-aegis-rag-error">
                        <X size={14} />
                    </button>
                </div>
            </div>
        </header>
    )
}
