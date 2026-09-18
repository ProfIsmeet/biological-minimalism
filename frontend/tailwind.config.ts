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
        // Master-prompt §6.2 jury/experimental design tokens. Additive to the
        // existing space/cyan/signal palette (still used by non-primary-nav
        // routes like /ai-insights and /research's preserved Stage-3/4 views);
        // do not remove those while this coexists.
        canvas: "#0B0F12",
        "jury-sidebar": "#0E1418",
        surface: {
          1: "#11181C",
          2: "#151E23",
          3: "#1A242A",
        },
        "jury-border": {
          subtle: "#243038",
          strong: "#34434C",
        },
        ink: {
          primary: "#F2F5F6",
          secondary: "#B5C0C6",
          muted: "#7F8E97",
          disabled: "#56636B",
        },
        "final-accent": {
          DEFAULT: "#63AAA2",
          hover: "#79BDB5",
          soft: "rgba(99, 170, 162, 0.12)",
        },
        information: {
          DEFAULT: "#789BC2",
          soft: "rgba(120, 155, 194, 0.12)",
        },
        experimental: {
          DEFAULT: "#C69A58",
          soft: "rgba(198, 154, 88, 0.12)",
        },
        "jury-warning": {
          DEFAULT: "#D0A45F",
          soft: "rgba(208, 164, 95, 0.12)",
        },
        "jury-fault": {
          DEFAULT: "#CF6D6D",
          soft: "rgba(207, 109, 109, 0.12)",
        },
        "jury-success": {
          DEFAULT: "#69A98B",
          soft: "rgba(105, 169, 139, 0.12)",
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
