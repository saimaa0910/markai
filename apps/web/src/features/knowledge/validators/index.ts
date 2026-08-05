/**
 * @file index.ts
 * @description Validators for Knowledge feature.
 */

export function validateSupportedFileType(filename: string): boolean {
  const allowedExtensions = ['pdf', 'txt', 'md', 'docx'];
  const ext = filename.split('.').pop()?.toLowerCase();
  return ext ? allowedExtensions.includes(ext) : false;
}
