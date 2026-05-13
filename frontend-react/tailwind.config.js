/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent: '#f0a030',
        'accent-soft': 'rgba(240,160,48,0.15)',
        'accent-glow': 'rgba(240,160,48,0.08)',
        surface: 'rgba(18,18,24,0.95)',
        'surface2': 'rgba(255,255,255,0.04)',
        border: 'rgba(255,255,255,0.08)',
        muted: 'rgba(255,255,255,0.4)',
      },
      fontFamily: {
        display: ['Outfit', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};