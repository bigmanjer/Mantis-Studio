import { Bebas_Neue, Cinzel, Fredoka, Playfair_Display } from "next/font/google";

// Display faces for typeset covers (the app's own Literata/Inter cover "Classic" and "Clean").
const playfair = Playfair_Display({ subsets: ["latin"], weight: ["600", "800"], style: ["normal", "italic"], display: "swap" });
const cinzel = Cinzel({ subsets: ["latin"], weight: ["600", "800"], display: "swap" });
const bebas = Bebas_Neue({ subsets: ["latin"], weight: "400", display: "swap" });
const fredoka = Fredoka({ subsets: ["latin"], weight: ["500", "700"], display: "swap" });

export const COVER_FONTS = {
  Elegant: { family: playfair.style.fontFamily, weight: 800, upper: false, spacing: 0 },
  Epic: { family: cinzel.style.fontFamily, weight: 800, upper: true, spacing: 0.08 },
  Thriller: { family: bebas.style.fontFamily, weight: 400, upper: true, spacing: 0.04 },
  Playful: { family: fredoka.style.fontFamily, weight: 700, upper: false, spacing: 0 },
  Classic: { family: "var(--font-literata), Georgia, serif", weight: 700, upper: false, spacing: 0 },
} as const;
export type CoverFont = keyof typeof COVER_FONTS;
