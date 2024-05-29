import {nextui} from '@nextui-org/theme';
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@nextui-org/theme/dist/components/(button|image).js"
  ],
  theme: {
    extend: {
      fontFamily: {
        playfair: ['Playfair Display', "serif"],
        "gt-walsheim-medium": ["GTWalsheimPro-Medium", "sans-serif"],
        parisienne: ['Parisienne', "cursive"]
      }
    },
    screens: {
      phone: "360px",
      xs: "480px",
      s: "624px",
      sm: "768px",
      tablet: "914px",
      md: "1060px",
      lg: "1200px",
      xl: "1700px",
    },
  },
  plugins: [nextui()],
};
export default config;
