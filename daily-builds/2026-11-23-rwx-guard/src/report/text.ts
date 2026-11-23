import pc from 'picocolors';
import type { ReplayStats } from '../audit/replay.js';

export function formatTextReport(stats: ReplayStats, useColor: boolean = true): string {
  const c = useColor ? pc : createNoColor();
  
  const lines: string[] = [];
  
  lines.push(c.bold('Audit Report'));
  lines.push('');
  lines.push(`Total calls: ${stats.total}`);
  lines.push(`  ${c.green('Allowed')}: ${stats.byVerdict['allow'] || 0}`);
  lines.push(`  ${c.red('Denied')}: ${stats.byVerdict['deny'] || 0}`);
  lines.push(`  ${c.yellow('Ask')}: ${stats.byVerdict['ask'] || 0}`);
  lines.push('');

  if (stats.topDeniedRules.length > 0) {
    lines.push(c.bold('Top Denied Rules:'));
    for (const { ruleId, count } of stats.topDeniedRules) {
      lines.push(`  ${ruleId}: ${count} denials`);
    }
    lines.push('');
  }

  if (stats.riskiestCalls.length > 0) {
    lines.push(c.bold('Riskiest Calls:'));
    for (const { call, decision } of stats.riskiestCalls.slice(0, 5)) {
      lines.push(`  ${c.red('✗')} ${call.tool} (${call.agent})`);
      lines.push(`    ${decision.reason}`);
    }
    lines.push('');
  }

  return lines.join('\n');
}

function createNoColor() {
  const identity = (s: string) => s;
  return {
    bold: identity,
    green: identity,
    red: identity,
    yellow: identity,
  };
}
