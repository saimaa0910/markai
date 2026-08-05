/**
 * @file index.ts
 * @description Validators for SEO feature.
 */

export function validateKeywordTerm(term: string): boolean {
  return term.trim().length > 0;
}
