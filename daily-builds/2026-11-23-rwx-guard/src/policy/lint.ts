import type { Policy } from './schema.js';

export interface LintIssue {
  severity: 'error' | 'warning';
  ruleId?: string;
  message: string;
}

export interface LintResult {
  issues: LintIssue[];
  passed: boolean;
}

export function lintPolicy(policy: Policy): LintResult {
  const issues: LintIssue[] = [];

  if (!policy.rules || policy.rules.length === 0) {
    issues.push({
      severity: 'warning',
      message: 'Policy has no rules defined',
    });
  }

  if (policy.rules) {
    for (let i = 0; i < policy.rules.length; i++) {
      const rule = policy.rules[i];
      if (!rule) continue;

      if (!rule.reason || rule.reason.trim() === '') {
        issues.push({
          severity: 'warning',
          ruleId: rule.id,
          message: `Rule "${rule.id}" is missing a reason`,
        });
      }

      if (rule.match.tool === '*' && rule.decision === 'allow') {
        issues.push({
          severity: 'warning',
          ruleId: rule.id,
          message: `Rule "${rule.id}" allows all tools (*), which is overly broad`,
        });
      }

      for (let j = i + 1; j < policy.rules.length; j++) {
        const otherRule = policy.rules[j];
        if (!otherRule) continue;

        const earlier = policy.rules[i];
        if (!earlier) continue;

        if (isRuleShadowed(earlier, otherRule)) {
          issues.push({
            severity: 'warning',
            ruleId: otherRule.id,
            message: `Rule "${otherRule.id}" is shadowed by earlier rule "${earlier.id}" and will never match`,
          });
        }
      }
    }
  }

  const passed = issues.length === 0;
  return { issues, passed };
}

function isRuleShadowed(earlier: NonNullable<Policy['rules']>[number], later: NonNullable<Policy['rules']>[number]): boolean {
  if (!earlier.match.tool && !earlier.match.agent && !earlier.match.args) {
    return true;
  }

  if (earlier.match.tool && later.match.tool) {
    if (earlier.match.tool === '*' || earlier.match.tool === later.match.tool) {
      if (!earlier.match.agent && !later.match.agent) {
        if (!earlier.match.args && !later.match.args) {
          return true;
        }
      }
    }
  }

  return false;
}
