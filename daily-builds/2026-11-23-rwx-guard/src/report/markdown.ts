import type { ReplayStats } from '../audit/replay.js';

export function formatMarkdownReport(stats: ReplayStats): string {
  const lines: string[] = [];
  
  lines.push('# Audit Report');
  lines.push('');
  lines.push(`**Total calls:** ${stats.total}`);
  lines.push('');
  lines.push('## Verdict Breakdown');
  lines.push('');
  lines.push('| Verdict | Count |');
  lines.push('|---------|-------|');
  lines.push(`| Allowed | ${stats.byVerdict['allow'] || 0} |`);
  lines.push(`| Denied | ${stats.byVerdict['deny'] || 0} |`);
  lines.push(`| Ask | ${stats.byVerdict['ask'] || 0} |`);
  lines.push('');

  if (stats.topDeniedRules.length > 0) {
    lines.push('## Top Denied Rules');
    lines.push('');
    lines.push('| Rule ID | Denials |');
    lines.push('|---------|---------|');
    for (const { ruleId, count } of stats.topDeniedRules) {
      lines.push(`| ${ruleId} | ${count} |`);
    }
    lines.push('');
  }

  if (stats.riskiestCalls.length > 0) {
    lines.push('## Riskiest Calls');
    lines.push('');
    for (const { call, decision } of stats.riskiestCalls.slice(0, 5)) {
      lines.push(`- **${call.tool}** (${call.agent})`);
      lines.push(`  - ${decision.reason}`);
    }
    lines.push('');
  }

  return lines.join('\n');
}
