/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        deepnavy: '#0D132B',
        electric: '#2563EB',
        purplebrand: '#7C3AED',
        magentabrand: '#E11DFA',
        tealbrand: '#06B6D4',
        lightbrand: '#F1F5F9',
        slatebrand: '#1F2937'
      },
      boxShadow: {
        glow: '0 24px 80px rgba(37, 99, 235, 0.20)',
        card: '0 24px 60px rgba(13, 19, 43, 0.10)'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Arial', 'sans-serif']
      }
    }
  },
  plugins: []
};
