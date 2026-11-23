import type { Rule, Decision } from './policy/schema.js';

export interface ExplainStep {
  ruleId?: string;
  matched: boolean;
  reason: string;
}

export interface ExplainTrace {
  steps: ExplainStep[];
  finalDecision: Decision;
  finalReason: string;
}

export function createExplain(): {
  add(step: ExplainStep): void;
  build(decision: Decision, reason: string): ExplainTrace;
} {
  const steps: ExplainStep[] = [];

  return {
    add(step: ExplainStep) {
      steps.push(step);
    },

    build(decision: Decision, reason: string): ExplainTrace {
      return {
        steps,
        finalDecision: decision,
        finalReason: reason,
      };
    },
  };
}
