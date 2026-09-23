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
        // Prompt-3 §5.2 exact jury/experimental design-system palette.
        // Additive to the legacy space/cyan/signal palette (still used by
        // non-primary-nav reference routes like /ai-insights,
        // /mission-timeline, /settings, and /research's preserved Stage-3/4
        // views); do not remove those while this coexists.
        canvas: "#081013",
        "jury-sidebar": "#0B1418",
        surface: {
          1: "#0D181C",
          2: "#111E23",
          3: "#16262C",
        },
        "jury-border": {
          subtle: "#203239",
          strong: "#30464F",
        },
        ink: {
          primary: "#F2F6F7",
          secondary: "#B6C4C9",
          muted: "#758990",
          disabled: "#516269",
        },
        "final-accent": {
          DEFAULT: "#69B7AD",
          hover: "#7FC5BC",
          soft: "rgba(105, 183, 173, 0.12)",
        },
        information: {
          DEFAULT: "#79A7D3",
          soft: "rgba(121, 167, 211, 0.12)",
        },
        experimental: {
          DEFAULT: "#C79A5B",
          soft: "rgba(199, 154, 91, 0.12)",
        },
        "jury-warning": {
          DEFAULT: "#D5A45E",
          soft: "rgba(213, 164, 94, 0.12)",
        },
        "jury-fault": {
          DEFAULT: "#D46F70",
          soft: "rgba(212, 111, 112, 0.12)",
        },
        "jury-success": {
          DEFAULT: "#72B491",
          soft: "rgba(114, 180, 145, 0.12)",
        },
        modality: {
          ppg: "#56C5B5",
          imu: "#7D9FD3",
          ecg: "#D97979",
          eeg: "#A58BD0",
          eog: "#D0A25E",
        },
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "SF Mono",
          "Menlo",
          "Consolas",
          "monospace",
        ],
        sans: [
          "Helvetica Neue",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
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
