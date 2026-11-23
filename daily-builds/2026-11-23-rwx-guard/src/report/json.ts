import type { ReplayStats } from '../audit/replay.js';

export function formatJsonReport(stats: ReplayStats): string {
  return JSON.stringify(stats, null, 2);
}
