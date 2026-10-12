/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Map CSS custom properties so Tailwind classes stay in sync with tokens
        ink: {
          950: 'var(--color-ink-950)',
          900: 'var(--color-ink-900)',
          850: 'var(--color-ink-850)',
          800: 'var(--color-ink-800)',
          750: 'var(--color-ink-750)',
          700: 'var(--color-ink-700)',
          600: 'var(--color-ink-600)',
          400: 'var(--color-ink-400)',
          300: 'var(--color-ink-300)',
          200: 'var(--color-ink-200)',
          100: 'var(--color-ink-100)',
          50:  'var(--color-ink-50)',
        },
        trafo: {
          DEFAULT: 'var(--color-trafo-blue)',
          hover:   'var(--color-trafo-blue-hover)',
          tint:    'var(--color-trafo-blue-tint)',
        },
        warn: {
          DEFAULT: 'var(--color-warn-amber)',
          bg:      'var(--color-warn-amber-bg)',
          border:  'var(--color-warn-amber-border)',
        },
        crit: {
          DEFAULT: 'var(--color-crit-red)',
          bg:      'var(--color-crit-red-bg)',
          border:  'var(--color-crit-red-border)',
        },
        safe: {
          DEFAULT: 'var(--color-safe-green)',
          bg:      'var(--color-safe-green-bg)',
          border:  'var(--color-safe-green-border)',
        },
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        mono: 'var(--font-mono)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      spacing: {
        // Named spacing tokens
        '0.5': '2px',
        '1':   '4px',
        '2':   '8px',
        '3':   '12px',
        '4':   '16px',
        '5':   '20px',
        '6':   '24px',
        '8':   '32px',
        '10':  '40px',
        '12':  '48px',
        '16':  '64px',
      },
    },
  },
  plugins: [],
}
