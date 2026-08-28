import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        space: {
          950: "#04070d",
          900: "#070b14",
          850: "#0a0f1c",
          800: "#0d1424",
          700: "#131c33",
          600: "#1b2743",
          500: "#263355",
        },
        cyan: {
          400: "#4fd8e8",
          500: "#2bc4dd",
          600: "#17a3bd",
        },
        signal: {
          nominal: "#33e0a1",
          warning: "#f5b942",
          critical: "#ff5c66",
          offline: "#5a6786",
        },
        amber: {
          400: "#ffb545",
          500: "#ff9d1f",
        },
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "Cascadia Code",
          "SFMono-Regular",
          "Consolas",
          "Menlo",
          "monospace",
        ],
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        glow: "0 0 24px -4px rgba(79, 216, 232, 0.45)",
        "glow-amber": "0 0 24px -4px rgba(255, 181, 69, 0.45)",
        "glow-critical": "0 0 24px -4px rgba(255, 92, 102, 0.45)",
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 0 0 1px rgba(255,255,255,0.04)",
      },
      backgroundImage: {
        starfield:
          "radial-gradient(1px 1px at 20% 30%, rgba(255,255,255,0.5) 0, transparent 100%), radial-gradient(1px 1px at 60% 70%, rgba(255,255,255,0.35) 0, transparent 100%), radial-gradient(1.5px 1.5px at 85% 20%, rgba(255,255,255,0.45) 0, transparent 100%), radial-gradient(1px 1px at 40% 85%, rgba(255,255,255,0.3) 0, transparent 100%)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { transform: "scale(0.9)", opacity: "0.7" },
          "80%": { transform: "scale(1.6)", opacity: "0" },
          "100%": { transform: "scale(1.6)", opacity: "0" },
        },
        scanline: {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "0 -200px" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.2,0.6,0.4,1) infinite",
        scanline: "scanline 6s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
