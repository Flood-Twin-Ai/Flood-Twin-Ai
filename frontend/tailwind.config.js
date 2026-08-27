/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // JAL-DRISHTI control-room palette
        basin: {
          950: "#070B14", // page background — deep monsoon night
          900: "#0B1220", // panel background
          800: "#111A2C", // card background
          700: "#1B2740", // borders / dividers
          600: "#2B3A5C", // hover / raised
        },
        tide: {
          400: "#5EEAD4",
          500: "#2DD4BF", // primary accent — teal water
          600: "#14B8A6",
        },
        risk: {
          low: "#34D399",
          moderate: "#FBBF24",
          high: "#F97316",
          critical: "#EF4444",
        },
        mist: {
          300: "#B7C3D9", // secondary text
          500: "#7C8AA8", // muted text
        },
      },
      fontFamily: {
        display: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(45,212,191,0.06), 0 20px 40px -20px rgba(0,0,0,0.6)",
      },
      keyframes: {
        ripple: {
          "0%": { transform: "scale(0.4)", opacity: "0.7" },
          "100%": { transform: "scale(2.2)", opacity: "0" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
      },
      animation: {
        ripple: "ripple 2.2s cubic-bezier(0.2,0.6,0.4,1) infinite",
        pulseDot: "pulseDot 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
