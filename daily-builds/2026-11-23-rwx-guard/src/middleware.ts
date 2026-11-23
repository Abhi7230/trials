import type { Guard } from './engine.js';
import { PolicyDeniedError } from './errors.js';

export interface ToolMeta {
  agent: string;
  tool: string;
}

export interface MiddlewareOptions {
  onAsk?: (decision: any) => void | Promise<void>;
}

export function guardTool<T extends (...args: any[]) => any>(
  fn: T,
  guard: Guard,
  meta: ToolMeta,
  options: MiddlewareOptions = {}
): T {
  return ((...args: any[]) => {
    const toolArgs = args[0] as Record<string, unknown> || {};
    
    const decision = guard.check({
      agent: meta.agent,
      tool: meta.tool,
      args: toolArgs,
    });

    if (decision.verdict === 'deny') {
      throw new PolicyDeniedError(
        `Policy denied: ${decision.reason}`,
        decision
      );
    }

    if (decision.verdict === 'ask') {
      if (options.onAsk) {
        options.onAsk(decision);
        throw new PolicyDeniedError(
          `Policy requires approval: ${decision.reason}`,
          decision
        );
      } else {
        throw new PolicyDeniedError(
          `Policy requires approval (no handler): ${decision.reason}`,
          decision
        );
      }
    }

    return fn(...args);
  }) as T;
}

export function withGuard<T extends Record<string, (...args: any[]) => any>>(
  toolMap: T,
  guard: Guard,
  meta: Omit<ToolMeta, 'tool'>,
  options: MiddlewareOptions = {}
): T {
  const wrapped: any = {};

  for (const [toolName, fn] of Object.entries(toolMap)) {
    wrapped[toolName] = guardTool(fn, guard, { ...meta, tool: toolName }, options);
  }

  return wrapped;
}
