/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          red: '#DA291C',
          gray6: '#A7A8AA',
          gray10: '#63666A',
          black: '#2D2926',
          charcoal: '#1F1C1A',
          paper: '#F4F0E8',
          paperAlt: '#E8E2D7',
          ink: '#292522',
          reference: {
            canvas: '#27282C',
            shell: '#272928',
            panel: '#28292B',
            panelDeep: '#05070D',
            text: '#D8DADE',
            muted: '#AEB3BC',
            line: '#536078',
            red: '#DD2B1F',
            white: '#F4F5F6',
          },
        },
      },
      fontFamily: {
        display: ['Cormorant Garamond', 'Playfair Display', 'Georgia', 'serif'],
        serifBody: ['PT Serif', 'Georgia', 'serif'],
        body: ['PT Sans', 'Helvetica Neue', 'Arial', 'sans-serif'],
        referenceHeading: ['"Times New Roman"', 'Times', 'serif'],
        referenceBody: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        formal: '0 24px 70px rgba(0, 0, 0, 0.26)',
        referenceCard: '0 0 0 1px rgba(83, 96, 120, 0.22), 0 12px 34px rgba(0, 0, 0, 0.26), 0 0 24px rgba(35, 78, 160, 0.16)',
        symbolCard: '0 0 0 1px rgba(83, 96, 120, 0.18), 0 10px 26px rgba(0, 0, 0, 0.3), 0 0 18px rgba(37, 83, 166, 0.22)',
        calendarToday: '0 0 10px rgba(83, 96, 120, 0.28)',
        headerGlow: '0 1px 0 rgba(244, 245, 246, 0.82)',
      },
    },
  },
  plugins: [],
};
