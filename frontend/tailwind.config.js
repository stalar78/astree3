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
        },
      },
      fontFamily: {
        display: ['Cormorant Garamond', 'Playfair Display', 'Georgia', 'serif'],
        serifBody: ['PT Serif', 'Georgia', 'serif'],
        body: ['PT Sans', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        formal: '0 24px 70px rgba(0, 0, 0, 0.26)',
      },
    },
  },
  plugins: [],
};
