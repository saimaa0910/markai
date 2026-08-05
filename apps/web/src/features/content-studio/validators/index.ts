/**
 * @file index.ts
 * @description Validators for Content Studio.
 */

export function validateWordCount(text: string, minWords: number): boolean {
  const words = text.trim().split(/\s+/).filter(Boolean);
  return words.length >= minWords;
}
