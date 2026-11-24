export interface Project {
  id: string;
  user_id: string;
  title: string;
  author: string;
  genre: string;
  premise: string;
  outline: string;
  canon_rules: string;
  style_guide: string;
  target_words: number;
  style_dials?: Record<string, number> | null;
  /** Keep the World Bible, canon rules and summaries updated by AI as the writer works (default on). */
  auto_canon?: boolean;
  /** Let the AI read the Knowledge Base for this book (default on). */
  use_knowledge?: boolean;
  /** Up to 3 author style lenses (names from the built-in library). */
  style_lenses?: string[];
  created_at: string;
  updated_at: string;
}

export interface Chapter {
  id: string;
  project_id: string;
  position: number;
  title: string;
  content: string;
  summary: string;
  word_count: number;
  updated_at: string;
}

export const ENTITY_CATEGORIES = ["Character", "Location", "Item", "Faction", "Lore"] as const;
export type EntityCategory = (typeof ENTITY_CATEGORIES)[number];

export interface Entity {
  id: string;
  project_id: string;
  name: string;
  category: EntityCategory;
  description: string;
  aliases: string[];
  created_at: string;
}

export function countWords(text: string): number {
  const m = text.trim().match(/\S+/g);
  return m ? m.length : 0;
}
