/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        phantom: {
          bg: "#030712",
          surface: "#0d1117",
          border: "#1a2332",
          red: "#ef4444",
          "red-glow": "#dc2626",
          orange: "#f97316",
          cyan: "#06b6d4",
          "cyan-glow": "#0891b2",
          purple: "#a855f7",
          "purple-glow": "#9333ea",
          yellow: "#eab308",
          green: "#22c55e",
          muted: "#6b7280",
          text: "#e2e8f0",
          "text-dim": "#94a3b8",
        },
      },
      animation: {
        "pulse-red": "pulse-red 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-cyan": "pulse-cyan 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-purple": "pulse-purple 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "scan": "scan 3s linear infinite",
        "float": "float 6s ease-in-out infinite",
        "glow-red": "glow-red 2s ease-in-out infinite alternate",
      },
      keyframes: {
        "pulse-red": {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 20px rgba(239, 68, 68, 0.5)" },
          "50%": { opacity: "0.5", boxShadow: "0 0 5px rgba(239, 68, 68, 0.2)" },
        },
        "pulse-cyan": {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 20px rgba(6, 182, 212, 0.5)" },
          "50%": { opacity: "0.5", boxShadow: "0 0 5px rgba(6, 182, 212, 0.2)" },
        },
        "pulse-purple": {
          "0%, 100%": { opacity: "1", boxShadow: "0 0 20px rgba(168, 85, 247, 0.5)" },
          "50%": { opacity: "0.5", boxShadow: "0 0 5px rgba(168, 85, 247, 0.2)" },
        },
        "scan": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "glow-red": {
          from: { textShadow: "0 0 10px rgba(239, 68, 68, 0.5)" },
          to: { textShadow: "0 0 20px rgba(239, 68, 68, 0.9), 0 0 40px rgba(239, 68, 68, 0.4)" },
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      boxShadow: {
        "red-glow": "0 0 20px rgba(239, 68, 68, 0.4)",
        "cyan-glow": "0 0 20px rgba(6, 182, 212, 0.4)",
        "purple-glow": "0 0 20px rgba(168, 85, 247, 0.4)",
        "orange-glow": "0 0 20px rgba(249, 115, 22, 0.4)",
        "panel": "0 0 0 1px rgba(26, 35, 50, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.02)",
      },
    },
  },
  plugins: [],
};
