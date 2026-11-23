import type { Guard, Decision } from '../engine.js';
import type { AuditCall } from './parse.js';

export interface ReplayResult {
  total: number;
  allowed: number;
  denied: number;
  ask: number;
  calls: Array<{
    call: AuditCall;
    decision: Decision;
  }>;
}

export interface ReplayStats {
  total: number;
  byVerdict: Record<string, number>;
  topDeniedRules: Array<{ ruleId: string; count: number }>;
  riskiestCalls: Array<{ call: AuditCall; decision: Decision }>;
}

export function replayCalls(calls: AuditCall[], guard: Guard): ReplayResult {
  const results: ReplayResult = {
    total: calls.length,
    allowed: 0,
    denied: 0,
    ask: 0,
    calls: [],
  };

  for (const call of calls) {
    const decision = guard.check({
      agent: call.agent,
      tool: call.tool,
      args: call.args,
    });

    results.calls.push({ call, decision });

    if (decision.verdict === 'allow') {
      results.allowed++;
    } else if (decision.verdict === 'deny') {
      results.denied++;
    } else if (decision.verdict === 'ask') {
      results.ask++;
    }
  }

  return results;
}

export function computeStats(result: ReplayResult): ReplayStats {
  const byVerdict: Record<string, number> = {
    allow: result.allowed,
    deny: result.denied,
    ask: result.ask,
  };

  const deniedRules = new Map<string, number>();
  const deniedCalls: Array<{ call: AuditCall; decision: Decision }> = [];

  for (const { call, decision } of result.calls) {
    if (decision.verdict === 'deny') {
      deniedCalls.push({ call, decision });
      
      if (decision.ruleId) {
        deniedRules.set(decision.ruleId, (deniedRules.get(decision.ruleId) || 0) + 1);
      }
    }
  }

  const topDeniedRules = Array.from(deniedRules.entries())
    .map(([ruleId, count]) => ({ ruleId, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const riskiestCalls = deniedCalls.slice(0, 10);

  return {
    total: result.total,
    byVerdict,
    topDeniedRules,
    riskiestCalls,
  };
}
