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
  /** Fix clear continuity slips automatically while writing (default on). */
  auto_fix?: boolean;
  /** The chosen cover (book_images) and its title layout. */
  cover_id?: string | null;
  cover_style?: Record<string, unknown> | null;
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
  /** True when the AI wrote the summary; it then refreshes as the chapter changes. */
  summary_auto?: boolean;
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

export const LINK_KINDS = ["ally", "rival", "family", "love", "mentor", "enemy", "mystery", "other"] as const;
export type LinkKind = (typeof LINK_KINDS)[number];

/** A relationship the writer drew between two World Bible entries. */
export interface EntityLink {
  id: string;
  project_id: string;
  source_id: string;
  target_id: string;
  kind: LinkKind;
  note: string;
}

export function countWords(text: string): number {
  const m = text.trim().match(/\S+/g);
  return m ? m.length : 0;
}
