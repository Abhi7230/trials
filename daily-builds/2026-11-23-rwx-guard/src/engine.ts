import type { Policy, Rule, Level, Decision as PolicyDecision } from './policy/schema.js';
import { isLevelSufficient } from './levels.js';
import { matchGlob } from './match/glob.js';
import { matchArgs } from './match/args.js';
import { redactSecrets } from './redact.js';
import { createBudgetTracker, type BudgetTracker } from './budget.js';
import { createExplain, type ExplainTrace } from './explain.js';

export interface ToolCall {
  agent: string;
  tool: string;
  args: Record<string, unknown>;
}

export interface Decision {
  verdict: PolicyDecision;
  ruleId?: string;
  level?: Level;
  reason: string;
  matched: string[];
  redactedArgs: Record<string, unknown>;
  trace?: ExplainTrace;
}

export interface GuardOptions {
  clock?: () => number;
  workspaceRoot?: string;
  explain?: boolean;
}

export interface Guard {
  check(call: ToolCall): Decision;
}

export function createGuard(policy: Policy, options: GuardOptions = {}): Guard {
  const clock = options.clock || (() => Date.now());
  const budgetTracker = policy.budgets ? createBudgetTracker(policy.budgets) : null;

  return {
    check(call: ToolCall): Decision {
      const explain = options.explain ? createExplain() : null;
      const redactedArgs = redactSecrets(call.args);

      if (budgetTracker) {
        const budgetResult = budgetTracker.check(call.tool, call.agent, clock());
        if (!budgetResult.allowed) {
          const decision: Decision = {
            verdict: 'deny',
            reason: budgetResult.reason || 'Budget exceeded',
            matched: ['budget'],
            redactedArgs,
          };
          if (explain) {
            explain.add({
              matched: true,
              reason: budgetResult.reason || 'Budget exceeded',
            });
            decision.trace = explain.build('deny', budgetResult.reason || 'Budget exceeded');
          }
          return decision;
        }
      }

      const toolLevel = getToolLevel(policy, call.tool);
      const levelSufficient = isLevelSufficient(toolLevel, policy.defaultLevel);

      if (policy.rules) {
        for (const rule of policy.rules) {
          const matchResult = matchRule(rule, call, options);
          
          if (explain) {
            explain.add({
              ruleId: rule.id,
              matched: matchResult.matched,
              reason: matchResult.matched ? rule.reason : 'Rule did not match',
            });
          }

          if (matchResult.matched) {
            if (budgetTracker) {
              budgetTracker.record(call.tool, call.agent, clock());
            }

            const decision: Decision = {
              verdict: rule.decision,
              ruleId: rule.id,
              level: rule.level,
              reason: rule.reason,
              matched: matchResult.reasons,
              redactedArgs,
            };

            if (explain) {
              decision.trace = explain.build(rule.decision, rule.reason);
            }

            if (policy.strict && rule.decision === 'allow') {
              for (const otherRule of policy.rules) {
                if (otherRule === rule) continue;
                const otherMatch = matchRule(otherRule, call, options);
                if (otherMatch.matched && otherRule.decision === 'deny') {
                  decision.verdict = 'deny';
                  decision.ruleId = otherRule.id;
                  decision.reason = `Strict mode: deny rule "${otherRule.id}" overrides allow`;
                  if (explain) {
                    decision.trace = explain.build('deny', decision.reason);
                  }
                  return decision;
                }
              }
            }

            return decision;
          }
        }
      }

      if (budgetTracker) {
        budgetTracker.record(call.tool, call.agent, clock());
      }

      if (!levelSufficient) {
        const reason = `Tool "${call.tool}" requires level "${toolLevel}" but policy grants "${policy.defaultLevel}"`;
        const decision: Decision = {
          verdict: 'deny',
          level: toolLevel,
          reason,
          matched: ['level'],
          redactedArgs,
        };
        if (explain) {
          explain.add({ matched: false, reason: 'No rules matched' });
          explain.add({ matched: true, reason });
          decision.trace = explain.build('deny', reason);
        }
        return decision;
      }

      const decision: Decision = {
        verdict: policy.defaultDecision,
        reason: `No matching rule, using default decision: ${policy.defaultDecision}`,
        matched: ['default'],
        redactedArgs,
      };

      if (explain) {
        explain.add({ matched: false, reason: 'No rules matched' });
        decision.trace = explain.build(policy.defaultDecision, decision.reason);
      }

      return decision;
    },
  };
}

function getToolLevel(policy: Policy, toolName: string): Level {
  if (!policy.tools) {
    return policy.defaultLevel;
  }

  for (const [pattern, def] of Object.entries(policy.tools)) {
    if (matchGlob(pattern, toolName)) {
      return def.level;
    }
  }

  return policy.defaultLevel;
}

interface MatchResult {
  matched: boolean;
  reasons: string[];
}

function matchRule(rule: Rule, call: ToolCall, options: GuardOptions): MatchResult {
  const reasons: string[] = [];

  if (rule.match.tool) {
    if (!matchGlob(rule.match.tool, call.tool)) {
      return { matched: false, reasons: [] };
    }
    reasons.push(`tool:"${call.tool}"`);
  }

  if (rule.match.agent) {
    if (!matchGlob(rule.match.agent, call.agent)) {
      return { matched: false, reasons: [] };
    }
    reasons.push(`agent:"${call.agent}"`);
  }

  if (rule.match.args) {
    const argsResult = matchArgs(call.args, rule.match.args, {
      workspaceRoot: options.workspaceRoot,
    });
    if (!argsResult.matched) {
      return { matched: false, reasons: [] };
    }
    if (argsResult.reason) {
      reasons.push(argsResult.reason);
    }
  }

  return { matched: true, reasons };
}
