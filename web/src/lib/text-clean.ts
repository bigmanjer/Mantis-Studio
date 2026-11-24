/** Models sometimes add markdown even when told not to. Writers never want stray asterisks in a manuscript. */
export function stripMarkdown(text: string): string {
  return stripThinking(text)
    .replace(/\*\*([^*\n]+?)\*\*/g, "$1")
    .replace(/__([^_\n]+?)__/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*]{3,}\s*$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Some reasoning models wrap their thinking in <think> tags; writers only want the answer. */
export function stripThinking(text: string): string {
  return normalizeChars(text.replace(/<think>[\s\S]*?(<\/think>|$)/g, ""));
}

/**
 * Some models write look-alike characters (non-breaking hyphens, narrow spaces, zero-width
 * marks). They look normal but break search, find-and-replace and word counts in a manuscript.
 */
export function normalizeChars(text: string): string {
  return text
    .replace(/[‐‑]/g, "-")
    .replace(/[   ]/g, " ")
    .replace(/[​‌‍⁠﻿]/g, "");
}

/** Light clean-up for text that is still arriving: hide bold markers and unfinished thinking. */
export function cleanPartial(text: string): string {
  return stripThinking(text).replace(/\*\*/g, "").replace(/^#{1,6}\s+/gm, "");
}
