import type { Policy } from '../policy/schema.js';
import type { AuditCall } from './parse.js';
import { stringify as stringifyYaml } from 'yaml';

export function suggestPolicy(calls: AuditCall[]): Policy {
  const tools = new Set<string>();
  const agents = new Set<string>();

  for (const call of calls) {
    tools.add(call.tool);
    agents.add(call.agent);
  }

  const policy: Policy = {
    version: 1,
    defaultLevel: 'execute',
    defaultDecision: 'deny',
    strict: false,
    tools: {},
    rules: [],
  };

  for (const tool of tools) {
    const level = inferToolLevel(tool);
    if (policy.tools) {
      policy.tools[tool] = {
        level,
        description: `Auto-generated from audit log`,
      };
    }
  }

  if (policy.rules) {
    for (const tool of tools) {
      policy.rules.push({
        id: `allow-${tool.replace(/[^a-z0-9]/gi, '-')}`,
        match: { tool },
        decision: 'allow',
        reason: `Allow ${tool} as seen in audit log`,
      });
    }

    policy.rules.push({
      id: 'deny-unseen',
      match: {},
      decision: 'deny',
      reason: 'Deny all tools not seen in audit log',
    });
  }

  return policy;
}

export function policyToYAML(policy: Policy): string {
  return stringifyYaml(policy);
}

function inferToolLevel(tool: string): 'read' | 'write' | 'execute' {
  const lowerTool = tool.toLowerCase();

  if (
    lowerTool.startsWith('read') ||
    lowerTool.startsWith('get') ||
    lowerTool.startsWith('list') ||
    lowerTool.startsWith('search') ||
    lowerTool.startsWith('find')
  ) {
    return 'read';
  }

  if (
    lowerTool.startsWith('write') ||
    lowerTool.startsWith('create') ||
    lowerTool.startsWith('update') ||
    lowerTool.startsWith('delete') ||
    lowerTool.startsWith('edit')
  ) {
    return 'write';
  }

  return 'execute';
}
