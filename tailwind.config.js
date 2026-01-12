/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#667eea',
          600: '#5a67d8',
        }
      },
      animation: {
        'pulse-slow': 'pulse 2s ease-in-out infinite',
      }
    },
  },
  plugins: [],
}
