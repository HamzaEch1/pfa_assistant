// markez/frontend/tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Covers files in src directory
  ],
  theme: {
    extend: {
      colors: {
        'bp-orange-bright': '#f0380c', // The brighter orange
        'bp-orange': '#ec6414',       // The second orange
        'bp-brown': '#2c0c04',        // The dark brown
        'bp-white': '#FFFFFF',        // Adding white for convenience
        'bp-blue': '#005A9E',         // BP Blue color
        'bp-blue-bright': '#004C80',  // Darker BP Blue for hover
        // You can add other standard colors if needed, like grays:
        'bp-gray-light': '#f8f9fa',   // Example light gray
        'bp-gray': '#e9ecef',         // Example gray
        'bp-gray-dark': '#6c757d',     // Example dark gray
        'bp-sidebar-bg': '#343a40',    // Example dark background for sidebar
        'bp-sidebar-hover': '#495057', // Example hover for sidebar items
        'bp-sidebar-selected': '#6c757d', // Example selected item in sidebar
        'bp-chat-bubble': '#f5f7f9',   // Chat bubble background for assistant
        'bp-text': '#2d3748',          // Main text color
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}