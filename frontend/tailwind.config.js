// tailwind.config.js – Tailwind scanning setup for pages, components, and utilities.
module.exports = {
  content: [
    './pages/**/*.{ts,tsx,js,jsx}',
    './components/**/*.{ts,tsx,js,jsx}',
    './lib/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        lena: {
          primary: '#1e678a',
          primaryHover: '#17506b',
          ring: '#b9e2f1',
          secondary: '#e6f3f7',
        },
      },
    },
  },
  plugins: [],
};
