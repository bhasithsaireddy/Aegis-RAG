/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Core Backgrounds (Monochrome theme)
                'aegis-rag-bg': {
                    app: 'rgb(var(--aegis-rag-bg-app) / <alpha-value>)',
                    panel: 'rgb(var(--aegis-rag-bg-panel) / <alpha-value>)',
                    card: 'rgb(var(--aegis-rag-bg-card) / <alpha-value>)',
                    elevated: 'rgb(var(--aegis-rag-bg-elevated) / <alpha-value>)',
                    hover: 'rgb(var(--aegis-rag-bg-hover) / <alpha-value>)',
                },
                // Text Hierarchy
                'aegis-rag-text': {
                    primary: 'rgb(var(--aegis-rag-text-primary) / <alpha-value>)',
                    secondary: 'rgb(var(--aegis-rag-text-secondary) / <alpha-value>)',
                    muted: 'rgb(var(--aegis-rag-text-muted) / <alpha-value>)',
                },
                // Accent System (Neutral monochrome)
                'aegis-rag-accent': {
                    DEFAULT: 'rgb(var(--aegis-rag-accent) / <alpha-value>)',
                    light: 'rgb(var(--aegis-rag-accent-light) / <alpha-value>)',
                    dark: 'rgb(var(--aegis-rag-accent-dark) / <alpha-value>)',
                    glow: 'rgba(255, 255, 255, 0.12)',
                },
                // Status Colors
                'aegis-rag-success': 'rgb(var(--aegis-rag-success) / <alpha-value>)',
                'aegis-rag-warning': 'rgb(var(--aegis-rag-warning) / <alpha-value>)',
                'aegis-rag-error': 'rgb(var(--aegis-rag-error) / <alpha-value>)',
                // Borders
                'aegis-rag-border': {
                    DEFAULT: 'rgb(var(--aegis-rag-border) / 0.08)',
                    light: 'rgb(var(--aegis-rag-border) / 0.14)',
                    accent: 'rgb(var(--aegis-rag-border) / 0.24)',
                },
            },
            fontFamily: {
                sans: ['Gantari', 'Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'Consolas', 'monospace'],
            },
            fontSize: {
                'xs': ['0.75rem', { lineHeight: '1rem' }],
                'sm': ['0.8125rem', { lineHeight: '1.25rem' }],
                'base': ['0.875rem', { lineHeight: '1.5rem' }],
                'lg': ['1rem', { lineHeight: '1.75rem' }],
                'xl': ['1.125rem', { lineHeight: '1.75rem' }],
                '2xl': ['1.25rem', { lineHeight: '2rem' }],
                '3xl': ['1.5rem', { lineHeight: '2rem' }],
                '4xl': ['2rem', { lineHeight: '2.5rem' }],
            },
            spacing: {
                'sidebar': '260px',
                'context': '320px',
                'topbar': '48px',
            },
            borderRadius: {
                'xl': '0.75rem',
                '2xl': '1rem',
                '3xl': '1.5rem',
                'full': '9999px',
            },
            animation: {
                'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
                'fade-in': 'fadeIn 0.3s ease-out',
                'slide-up': 'slideUp 0.3s ease-out',
            },
            keyframes: {
                glow: {
                    '0%': { boxShadow: '0 0 5px rgba(160, 255, 155, 0.2)' },
                    '100%': { boxShadow: '0 0 20px rgba(160, 255, 155, 0.4)' },
                },
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-accent': 'linear-gradient(135deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.03) 100%)',
                'gradient-card': 'linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0) 100%)',
            },
        },
    },
    plugins: [],
}
