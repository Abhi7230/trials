export type Level = 'zero' | 'read' | 'write' | 'execute';

export const LEVELS: Level[] = ['zero', 'read', 'write', 'execute'];

const LEVEL_VALUES: Record<Level, number> = {
  zero: 0,
  read: 1,
  write: 2,
  execute: 3,
};

export function compareLevel(required: Level, granted: Level): number {
  return LEVEL_VALUES[required] - LEVEL_VALUES[granted];
}

export function isLevelSufficient(required: Level, granted: Level): boolean {
  return compareLevel(required, granted) <= 0;
}

export function getLevelValue(level: Level): number {
  return LEVEL_VALUES[level];
}
