import type { Budget } from './policy/schema.js';

export interface BudgetTracker {
  check(tool: string, agent: string, timestamp: number): BudgetCheckResult;
  record(tool: string, agent: string, timestamp: number): void;
}

export interface BudgetCheckResult {
  allowed: boolean;
  reason?: string;
}

interface CallRecord {
  timestamp: number;
}

export function createBudgetTracker(budgets: Budget[]): BudgetTracker {
  const calls = new Map<string, CallRecord[]>();

  return {
    check(tool: string, agent: string, timestamp: number): BudgetCheckResult {
      for (const budget of budgets) {
        if (budget.tool === tool || budget.tool === '*') {
          const key = `${agent}:${budget.tool}`;
          const history = calls.get(key) || [];
          
          const windowStart = timestamp - budget.windowSec * 1000;
          const recentCalls = history.filter((c) => c.timestamp >= windowStart);

          if (recentCalls.length >= budget.max) {
            return {
              allowed: false,
              reason: `Budget exceeded: ${budget.max} calls per ${budget.windowSec}s for tool "${budget.tool}"`,
            };
          }
        }
      }

      return { allowed: true };
    },

    record(tool: string, agent: string, timestamp: number): void {
      for (const budget of budgets) {
        if (budget.tool === tool || budget.tool === '*') {
          const key = `${agent}:${budget.tool}`;
          const history = calls.get(key) || [];
          history.push({ timestamp });
          
          const windowStart = timestamp - budget.windowSec * 1000;
          const filtered = history.filter((c) => c.timestamp >= windowStart);
          calls.set(key, filtered);
        }
      }
    },
  };
}
