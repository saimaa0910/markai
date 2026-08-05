/**
 * @file notifications.test.ts
 * @description Unit tests for Notifications feature.
 */

import { countUnreadNotifications } from '../utils';

describe('Notifications Utility Unit Tests', () => {
  it('should count unread notifications accurately', () => {
    const items = [{ read: true }, { read: false }, { read: false }];
    expect(countUnreadNotifications(items)).toBe(2);
  });
});
