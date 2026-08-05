/**
 * Content Studio Query Key Factory.
 */

export const contentKeys = {
  all: ['content-studio'] as const,
  list: () => [...contentKeys.all, 'list'] as const,
};
