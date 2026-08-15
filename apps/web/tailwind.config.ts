import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(220, 20%, 8%)",
        surface: "hsl(220, 18%, 12%)",
        "surface-elevated": "hsl(220, 16%, 16%)",
        "text-primary": "hsl(220, 10%, 90%)",
        "text-secondary": "hsl(220, 10%, 60%)",
        brand: "hsl(38, 92%, 50%)",
        "status-green": "hsl(142, 71%, 45%)",
        "status-amber": "hsl(38, 92%, 50%)",
        "status-red": "hsl(0, 72%, 51%)",
        "status-blue": "hsl(217, 91%, 60%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)"],
        mono: ["var(--font-jetbrains-mono)"],
      },
    },
  },
  plugins: [],
};
export default config;
