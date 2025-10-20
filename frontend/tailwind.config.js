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
          primary: '#1e3a8a',
          secondary: '#e0e7ff',
        },
      },
    },
  },
  plugins: [],
};
