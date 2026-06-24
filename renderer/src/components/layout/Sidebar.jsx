import { MessageSquare, FolderOpen, Settings, Plus } from 'lucide-react'
import useStore from '../../store/store'
import BrandMark from './BrandMark'

/**
 * Sidebar - Left navigation panel
 * Contains logo, new chat button, navigation menu, and recent chat history
 */
export default function Sidebar() {
    const {
        activeView,
        setActiveView,
        startNewChat,
    } = useStore()

    const handleNewChat = () => {
        startNewChat()
        setActiveView('chat')
    }

    const navItems = [
        { id: 'chat', label: 'Chat', icon: MessageSquare },
        { id: 'documents', label: 'Documents', icon: FolderOpen },
        { id: 'settings', label: 'Settings', icon: Settings },
    ]

    return (
        <aside className="w-sidebar flex flex-col bg-aegis-rag-bg-app border-r border-aegis-rag-border">
            <div className="p-5 border-b border-aegis-rag-border">
                <BrandMark />
            </div>

            {/* New Chat Button */}
            <div className="p-4">
                <button
                    onClick={handleNewChat}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                >
                    <Plus size={18} />
                    <span>New Chat</span>
                </button>
            </div>

            {/* Navigation Menu */}
            <nav className="px-3">
                <ul className="space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon
                        const isActive = activeView === item.id

                        return (
                            <li key={item.id}>
                                <button
                                    onClick={() => setActiveView(item.id)}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-fast ${isActive
                                        ? 'nav-active text-aegis-rag-text-primary'
                                        : 'text-aegis-rag-text-secondary hover:text-aegis-rag-text-primary hover:bg-aegis-rag-bg-hover'
                                        }`}
                                >
                                        <Icon size={20} className={isActive ? 'text-aegis-rag-text-primary' : ''} />
                                    <span className="font-medium">{item.label}</span>
                                </button>
                            </li>
                        )
                    })}
                </ul>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-aegis-rag-border">
                <div className="flex items-center justify-between text-xs text-aegis-rag-text-muted">
                    <span>Aegis RAG</span>
                    <span>Offline Mode</span>
                </div>
            </div>
        </aside>
    )
}
