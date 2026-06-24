import { LayoutDashboard, FileText, MessageSquare, Cpu, Database, TrendingUp } from 'lucide-react'
import useStore from '../store/store'

/**
 * Dashboard - Overview view with system stats and quick actions
 */
export default function Dashboard() {
    const { systemInfo, backendStatus, documents, toggleIngestion, setActiveView } = useStore()

    const stats = [
        {
            label: 'Documents',
            value: systemInfo.totalDocuments || documents.length,
            icon: FileText,
            color: 'text-blue-400',
            bg: 'bg-blue-400/10',
        },
        {
            label: 'Chunks',
            value: systemInfo.totalChunks || 0,
            icon: Database,
            color: 'text-aegis-rag-text-secondary',
            bg: 'bg-aegis-rag-bg-elevated',
        },
        {
            label: 'Workspace',
            value: 'Monochrome',
            icon: MessageSquare,
            color: 'text-zinc-300',
            bg: 'bg-zinc-400/10',
        },
        {
            label: 'LLM Status',
            value: systemInfo.llmAvailable ? 'Online' : 'Offline',
            icon: Cpu,
            color: systemInfo.llmAvailable ? 'text-aegis-rag-success' : 'text-aegis-rag-error',
            bg: systemInfo.llmAvailable ? 'bg-aegis-rag-success/10' : 'bg-aegis-rag-error/10',
        },
    ]

    const quickActions = [
        {
            label: 'Start Chat',
            description: 'Ask questions about your documents',
            icon: MessageSquare,
            action: () => setActiveView('chat'),
            primary: true,
        },
        {
            label: 'Upload Documents',
            description: 'Add files to your knowledge base',
            icon: FileText,
            action: toggleIngestion,
        },
        {
            label: 'Open Documents',
            description: 'Browse your uploaded documents',
            icon: Database,
            action: () => setActiveView('documents'),
        },
    ]

    return (
        <main className="flex-1 flex flex-col bg-aegis-rag-bg-app overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-aegis-rag-border flex-shrink-0">
                <div className="flex items-center gap-3">
                    <LayoutDashboard size={24} className="text-aegis-rag-accent" />
                    <div>
                        <h1 className="text-xl font-semibold text-aegis-rag-text-primary">Dashboard</h1>
                        <p className="text-sm text-aegis-rag-text-muted">
                            Welcome to your offline intelligence workspace
                        </p>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
                <div className="max-w-5xl mx-auto space-y-8">
                    {/* Stats Grid */}
                    <section>
                        <h2 className="text-sm font-medium text-aegis-rag-text-muted uppercase tracking-wider mb-4">
                            Overview
                        </h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {stats.map((stat) => {
                                const Icon = stat.icon
                                return (
                                    <div key={stat.label} className="card p-5">
                                        <div className="flex items-center justify-between mb-3">
                                            <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center`}>
                                                <Icon size={20} className={stat.color} />
                                            </div>
                                            <TrendingUp size={14} className="text-aegis-rag-text-muted" />
                                        </div>
                                        <p className="text-2xl font-bold text-aegis-rag-text-primary mb-1">
                                            {stat.value}
                                        </p>
                                        <p className="text-sm text-aegis-rag-text-muted">{stat.label}</p>
                                    </div>
                                )
                            })}
                        </div>
                    </section>

                    {/* Quick Actions */}
                    <section>
                        <h2 className="text-sm font-medium text-aegis-rag-text-muted uppercase tracking-wider mb-4">
                            Quick Actions
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {quickActions.map((action) => {
                                const Icon = action.icon
                                return (
                                    <button
                                        key={action.label}
                                        onClick={action.action}
                                        className={`p-6 rounded-2xl text-left transition-fast group ${action.primary
                                                ? 'bg-gradient-to-br from-aegis-rag-accent/20 to-aegis-rag-accent/5 border border-aegis-rag-accent/30 hover:border-aegis-rag-accent/50'
                                                : 'bg-aegis-rag-bg-card border border-aegis-rag-border hover:border-aegis-rag-accent/30'
                                            }`}
                                    >
                                        <div className={`w-12 h-12 rounded-xl mb-4 flex items-center justify-center ${action.primary ? 'bg-aegis-rag-accent/20' : 'bg-aegis-rag-bg-elevated'
                                            }`}>
                                            <Icon size={24} className={action.primary ? 'text-aegis-rag-accent' : 'text-aegis-rag-text-secondary'} />
                                        </div>
                                        <h3 className="font-semibold text-aegis-rag-text-primary mb-1 group-hover:text-aegis-rag-accent transition-fast">
                                            {action.label}
                                        </h3>
                                        <p className="text-sm text-aegis-rag-text-muted">
                                            {action.description}
                                        </p>
                                    </button>
                                )
                            })}
                        </div>
                    </section>

                    {/* System Status */}
                    <section>
                        <h2 className="text-sm font-medium text-aegis-rag-text-muted uppercase tracking-wider mb-4">
                            System Status
                        </h2>
                        <div className="card p-6">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                <StatusItem
                                    label="Backend"
                                    status={backendStatus}
                                    value={backendStatus === 'connected' ? 'Online' : 'Offline'}
                                />
                                <StatusItem
                                    label="LLM Model"
                                    status={systemInfo.llmAvailable ? 'connected' : 'disconnected'}
                                    value={systemInfo.llmModel || 'Not loaded'}
                                />
                                <StatusItem
                                    label="Vector DB"
                                    status="connected"
                                    value="ChromaDB"
                                />
                                <StatusItem
                                    label="Mode"
                                    status="connected"
                                    value="Offline"
                                />
                            </div>
                        </div>
                    </section>

                </div>
            </div>
        </main>
    )
}

function StatusItem({ label, status, value }) {
    const getStatusClass = () => {
        switch (status) {
            case 'connected': return 'status-dot-connected'
            case 'disconnected': return 'status-dot-disconnected'
            default: return 'status-dot-checking'
        }
    }

    return (
        <div>
            <p className="text-xs text-aegis-rag-text-muted mb-1">{label}</p>
            <div className="flex items-center gap-2">
                <div className={`status-dot ${getStatusClass()}`} />
                <span className="text-sm font-medium text-aegis-rag-text-primary">{value}</span>
            </div>
        </div>
    )
}
