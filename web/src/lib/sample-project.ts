import { countWords } from "./types";

const ch1 =
  "The kiln had been cold for three winters, but the letter inside it was warm.\n\nMara turned it over twice before she recognized the handwriting. Her mother had always pressed too hard on the downstrokes, as if every word needed to be carved rather than written.\n\nOutside, the orchard stirred. It was the wrong season for blossom, and yet she could smell it through the cracked shutters: something sweet and bruised, like a song half-remembered.\n\n“You were never meant to read this,” the letter began. Mara sat down on the cold brick floor and read it anyway.";

/** A small, complete example book used for "Try a sample project". */
export const SAMPLE = {
  project: {
    title: "The Glass Orchard (sample)",
    genre: "Fantasy",
    author: "",
    premise:
      "A disgraced glassblower discovers that the orchard her family tends grows memories instead of fruit, and that someone is quietly harvesting them.",
    outline:
      "Chapter 1: The Letter — Mara finds her mother's unsent letter in the cold kiln.\nChapter 2: First Harvest — The orchard blooms out of season, and the fruit glows with other people's memories.\nChapter 3: The Collector — A stranger with bare hands offers to buy the whole crop.\nChapter 4: Night Picking — Mara learns what each harvested memory costs the person who lost it.",
    canon_rules: "Memories can only be harvested at night.\nMara is 27.\nThe kiln has been cold for three winters.",
    style_guide: "Close third person, past tense. Lyrical but spare.",
    target_words: 90000,
  },
  chapters: [
    { title: "The Letter", content: ch1, word_count: countWords(ch1), summary: "Mara finds her mother's unsent letter in the cold kiln." },
    { title: "First Harvest", content: "", word_count: 0, summary: "The orchard blooms out of season, and the fruit glows with other people's memories." },
    { title: "The Collector", content: "", word_count: 0, summary: "A stranger with bare hands offers to buy the whole crop." },
  ],
  entities: [
    { name: "Mara Vell", category: "Character", description: "Glassblower, 27. Stubborn, gifted, grieving her mother.", aliases: ["the glass girl"] },
    { name: "The Orchard", category: "Location", description: "Grows memories instead of fruit. Blooms out of season when something is wrong.", aliases: [] },
    { name: "Memory-glass", category: "Lore", description: "Glass blown around a harvested memory. Shatters if the memory is false.", aliases: [] },
  ],
};
