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
            canvas: '#0B0D12',
            shell: '#171918',
            panel: '#05070D',
            panelDeep: '#02040A',
            footer: '#081B46',
            text: '#D8DADE',
            muted: '#AEB3BC',
            line: '#2F4372',
            red: '#DD2B1F',
            white: '#F4F5F6',
            flagBlue: '#0039A6',
            flagRed: '#D52B1E',
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
        referenceCard: '0 0 0 1px rgba(47, 67, 114, 0.48), 0 12px 34px rgba(0, 0, 0, 0.44), 0 0 26px rgba(14, 49, 132, 0.22)',
        symbolCard: '0 0 0 1px rgba(47, 67, 114, 0.52), 0 10px 24px rgba(0, 0, 0, 0.42), 0 0 18px rgba(24, 58, 147, 0.3)',
        calendarToday: '0 0 10px rgba(70, 94, 153, 0.34)',
      },
    },
  },
  plugins: [],
};
