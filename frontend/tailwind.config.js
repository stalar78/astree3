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
            canvas: '#252A34',
            shell: '#25282C',
            panel: '#26292E',
            panelDeep: '#202328',
            text: '#D8DADE',
            muted: '#AEB3BC',
            line: '#536078',
            red: '#E32620',
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
        referenceCard: '0 16px 38px rgba(0, 0, 0, 0.18)',
      },
    },
  },
  plugins: [],
};
