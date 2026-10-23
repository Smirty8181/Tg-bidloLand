/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  theme: {
    extend: {
      colors: {
        gold: "#F5C518",
        "gold-soft": "#FFE066",
        crimson: "#FF4757",
        royal: "#4D8DFF",
        ink: "#06070B",
        panel: "#12151E",
        muted: "#8B93A9",
      },
      fontFamily: {
        display: ["Unbounded", "Manrope", "sans-serif"],
        sans: ["Manrope", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl: "20px",
        "2xl": "24px",
      },
      boxShadow: {
        glow: "0 0 40px rgba(245, 197, 24, 0.18)",
        card: "0 8px 32px rgba(0, 0, 0, 0.35)",
        dock: "0 12px 40px rgba(0, 0, 0, 0.5)",
      },
      animation: {
        float: "float 4s ease-in-out infinite",
        shimmer: "shimmer 2.5s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-4px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
      },
    },
  },
  plugins: [],
};
