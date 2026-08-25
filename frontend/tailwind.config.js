/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Space Grotesk"', "ui-sans-serif", "system-ui", "sans-serif"],
        display: ['"Archivo Black"', "ui-sans-serif", "sans-serif"],
        mono: ['"Space Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        success: { DEFAULT: "hsl(var(--success))", foreground: "hsl(var(--success-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
      },
      borderWidth: { 2: "2px", 3: "3px", DEFAULT: "2px" },
      borderColor: { DEFAULT: "hsl(var(--border))" },
      borderRadius: { none: "0", sm: "0", md: "0", lg: "0", xl: "0" },
      boxShadow: {
        hard: "var(--hard-shadow)",
        "hard-sm": "4px 4px 0 0 hsl(0 0% 7%)",
        "hard-accent": "5px 5px 0 0 hsl(var(--accent))",
      },
    },
  },
  plugins: [],
};
