/** Art styles for covers and illustrations (shared by the browser and the server). */
export const ART_STYLES: Record<string, string> = {
  Painted: "rich digital oil painting, dramatic lighting, painterly brushwork, professional book cover illustration",
  Watercolor: "delicate watercolor illustration, soft washes, textured paper, professional book art",
  Photographic: "cinematic photograph, shallow depth of field, moody natural light, award-winning photography",
  Minimal: "minimalist graphic design, bold simple shapes, limited color palette, flat vector art, striking negative space",
  "Picture book": "warm children's picture book illustration, gentle colors, soft shading, charming and expressive, storybook art",
  "Dark fantasy": "dark fantasy concept art, atmospheric, ominous, intricate detail, epic scale",
  Romance: "romantic soft-focus illustration, warm golden tones, elegant and dreamy",
  "Sci-fi": "science fiction concept art, sleek, luminous, vast scale, cinematic",
  Vintage: "vintage mid-century book cover illustration, screen-print texture, retro palette",
};

// Never let the model paint lettering: titles are typeset by MANTIS.
const NO_TEXT = "no text, no letters, no words, no title, no typography, no watermark, no signature";

export function fullPrompt(prompt: string, style?: string): string {
  const s = style && ART_STYLES[style] ? `, ${ART_STYLES[style]}` : "";
  return `${prompt.trim().slice(0, 1200)}${s}, ${NO_TEXT}`;
}
