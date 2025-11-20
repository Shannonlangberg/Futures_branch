/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'ready': '#3B82F6',      // Blue
        'in-progress': '#A855F7', // Purple
        'awaiting': '#14B8A6',    // Teal
        'completed': '#F59E0B',   // Gold
        'overdue': '#F97316',     // Amber
        'at-risk': '#EF4444',     // Red
      },
    },
  },
  plugins: [],
};










