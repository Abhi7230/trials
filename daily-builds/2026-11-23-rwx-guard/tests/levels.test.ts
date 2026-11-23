import { describe, it, expect } from 'vitest';
import { LEVELS, compareLevel, isLevelSufficient, getLevelValue } from '../src/levels.js';

describe('levels', () => {
  it('should have correct level ordering', () => {
    expect(LEVELS).toEqual(['zero', 'read', 'write', 'execute']);
  });

  it('should compare levels correctly', () => {
    expect(compareLevel('read', 'execute')).toBeLessThan(0);
    expect(compareLevel('execute', 'read')).toBeGreaterThan(0);
    expect(compareLevel('write', 'write')).toBe(0);
  });

  it('should check level sufficiency', () => {
    expect(isLevelSufficient('read', 'execute')).toBe(true);
    expect(isLevelSufficient('execute', 'read')).toBe(false);
    expect(isLevelSufficient('write', 'write')).toBe(true);
    expect(isLevelSufficient('zero', 'read')).toBe(true);
  });

  it('should get level values', () => {
    expect(getLevelValue('zero')).toBe(0);
    expect(getLevelValue('read')).toBe(1);
    expect(getLevelValue('write')).toBe(2);
    expect(getLevelValue('execute')).toBe(3);
  });
});
