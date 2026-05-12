/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        neon: {
          pink: "#ff2ea6",
          purple: "#9d00ff",
          blue: "#00e5ff",
          green: "#00ff9d",
          yellow: "#fff02e",
        },
        bg: {
          0: "#05050a",
          1: "#0b0b15",
          2: "#12122a",
          3: "#1a1a3a",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        display: ["Orbitron", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        glow: "glow 2s ease-in-out infinite alternate",
        "spin-slow": "spin 20s linear infinite",
      },
      keyframes: {
        glow: {
          "0%": { filter: "drop-shadow(0 0 5px currentColor)" },
          "100%": { filter: "drop-shadow(0 0 20px currentColor)" },
        },
      },
      backgroundImage: {
        "grid-neon":
          "linear-gradient(rgba(255,46,166,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.1) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};
