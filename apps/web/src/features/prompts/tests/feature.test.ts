/**
 * @file feature.test.ts
 * @description Unit tests for Prompts feature.
 */

import { renderPromptTemplate } from '../utils';

describe('Prompts Template Utilities Unit Tests', () => {
  it('should render variables into template', () => {
    const output = renderPromptTemplate('Hello {{name}}', { name: 'World' });
    expect(output).toBe('Hello World');
  });
});
