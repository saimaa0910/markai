/**
 * @file feature.test.ts
 * @description Unit tests for Knowledge feature.
 */

import { validateSupportedFileType } from '../validators';

describe('Knowledge Feature Validators Unit Tests', () => {
  it('should validate allowed file extensions', () => {
    expect(validateSupportedFileType('manual.pdf')).toBe(true);
    expect(validateSupportedFileType('script.exe')).toBe(false);
  });
});
