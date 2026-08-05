/**
 * SEO Query Key Factory.
 */

export const seoKeys = {
  all: ['seo'] as const,
  overview: () => [...seoKeys.all, 'overview'] as const,
};
