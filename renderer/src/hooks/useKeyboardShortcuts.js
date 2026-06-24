import { useEffect, useCallback } from 'react'

/**
 * Custom hook for global keyboard shortcuts
 * @param {Object} shortcuts - Object mapping shortcut keys to handler functions
 * 
 * Usage:
 * useKeyboardShortcuts({
 *   'ctrl+k': () => console.log('Ctrl+K pressed'),
 *   'ctrl+shift+p': () => console.log('Ctrl+Shift+P pressed'),
 * })
 */
export default function useKeyboardShortcuts(shortcuts) {
    const handleKeyDown = useCallback((event) => {
        // Don't trigger shortcuts when typing in inputs
        if (
            event.target.tagName === 'INPUT' ||
            event.target.tagName === 'TEXTAREA' ||
            event.target.isContentEditable
        ) {
            return
        }

        // Build the shortcut string
        const parts = []
        if (event.ctrlKey || event.metaKey) parts.push('ctrl')
        if (event.shiftKey) parts.push('shift')
        if (event.altKey) parts.push('alt')

        // Add the key (lowercase)
        const key = event.key.toLowerCase()
        if (!['control', 'shift', 'alt', 'meta'].includes(key)) {
            parts.push(key)
        }

        const shortcutKey = parts.join('+')

        // Check if we have a handler for this shortcut
        if (shortcuts[shortcutKey]) {
            event.preventDefault()
            shortcuts[shortcutKey]()
        }
    }, [shortcuts])

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [handleKeyDown])
}
