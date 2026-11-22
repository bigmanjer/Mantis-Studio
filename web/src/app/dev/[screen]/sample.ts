import type { ProjectSummary } from "@/components/app/ProjectsView";
import type { Chapter, Entity, Project } from "@/lib/types";

const now = Date.now();
const ago = (h: number) => new Date(now - h * 3600_000).toISOString();

export const SAMPLE_PROJECT: Project = {
  id: "p1",
  user_id: "u1",
  title: "The Glass Orchard",
  author: "A. Writer",
  genre: "Fantasy",
  premise:
    "A disgraced glassblower discovers that the orchard her family tends grows memories instead of fruit, and someone is harvesting them.",
  outline:
    "Chapter 1: The Letter — Mara finds her mother's unsent letter in the cold kiln.\nChapter 2: First Harvest — The orchard blooms out of season.\nChapter 3: The Collector — A stranger offers to buy the crop.\nChapter 4: Night Picking — Mara learns what the memories cost.",
  canon_rules: "Memories can only be harvested at night.\nMara is 27.\nThe kiln has been cold for three winters.",
  style_guide: "Close third person, past tense. Lyrical but spare.",
  target_words: 90000,
  created_at: ago(400),
  updated_at: ago(2),
};

const text =
  "The kiln had been cold for three winters, but the letter inside it was warm.\n\nMara turned it over twice before she recognized the handwriting. Her mother had always pressed too hard on the downstrokes, as if every word needed to be carved rather than written.\n\nOutside, the orchard stirred. It was the wrong season for blossom, and yet she could smell it through the cracked shutters: something sweet and bruised, like a song half-remembered.";

export const SAMPLE_CHAPTERS: Chapter[] = [
  { id: "c1", project_id: "p1", position: 1, title: "The Letter", content: text, summary: "Mara finds her mother's letter.", word_count: 2914, updated_at: ago(2) },
  { id: "c2", project_id: "p1", position: 2, title: "First Harvest", content: "", summary: "", word_count: 3402, updated_at: ago(30) },
  { id: "c3", project_id: "p1", position: 3, title: "The Collector", content: "", summary: "", word_count: 1288, updated_at: ago(50) },
  { id: "c4", project_id: "p1", position: 4, title: "Night Picking", content: "", summary: "", word_count: 0, updated_at: ago(50) },
];

export const SAMPLE_ENTITIES: Entity[] = [
  { id: "e1", project_id: "p1", name: "Mara Vell", category: "Character", description: "Disgraced glassblower, 27. Stubborn, gifted, grieving her mother.", aliases: ["the glass girl"], created_at: ago(100) },
  { id: "e2", project_id: "p1", name: "The Orchard", category: "Location", description: "Grows memories instead of fruit. Blooms out of season when something is wrong.", aliases: [], created_at: ago(100) },
  { id: "e3", project_id: "p1", name: "The Collector", category: "Character", description: "Arrives with the first frost. Bare hands despite the cold.", aliases: [], created_at: ago(40) },
  { id: "e4", project_id: "p1", name: "Memory-glass", category: "Lore", description: "Glass blown around a harvested memory. Shatters if the memory is false.", aliases: [], created_at: ago(20) },
];

export const SAMPLE_PROJECTS: ProjectSummary[] = [
  { id: "p1", title: "The Glass Orchard", genre: "Fantasy", premise: SAMPLE_PROJECT.premise, target_words: 90000, updated_at: ago(2), words: 7604, chapterCount: 4 },
  {
    id: "p2",
    title: "Signal Lost",
    genre: "Thriller",
    premise: "A night-shift radio operator hears her own voice calling for help, broadcasting from three days in the future.",
    target_words: 80000,
    updated_at: ago(72),
    words: 31250,
    chapterCount: 14,
  },
];
