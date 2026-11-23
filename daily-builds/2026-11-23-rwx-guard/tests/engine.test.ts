import { describe, it, expect } from 'vitest';
import { createGuard } from '../src/engine.js';
import { loadPolicy } from '../src/policy/load.js';

describe('engine', () => {
  it('should allow calls matching rules', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy);
    
    const decision = guard.check({
      agent: 'coder',
      tool: 'read_file',
      args: { path: 'src/index.ts' },
    });
    
    expect(decision.verdict).toBe('allow');
    expect(decision.ruleId).toBe('allow-read-src');
  });

  it('should deny calls violating rules', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy);
    
    const decision = guard.check({
      agent: 'attacker',
      tool: 'read_file',
      args: { path: '.env' },
    });
    
    expect(decision.verdict).toBe('deny');
  });

  it('should use default decision when no rules match', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy);
    
    const decision = guard.check({
      agent: 'coder',
      tool: 'unknown_tool',
      args: {},
    });
    
    expect(decision.verdict).toBe('deny');
  });

  it('should enforce level requirements', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy);
    
    const decision = guard.check({
      agent: 'coder',
      tool: 'shell',
      args: { command: 'ls' },
    });
    
    expect(decision.verdict).toBe('deny');
  });

  it('should redact secrets in args', () => {
    const policy = loadPolicy('fixtures/policy-dev.yaml');
    const guard = createGuard(policy);
    
    const decision = guard.check({
      agent: 'coder',
      tool: 'api_call',
      args: { apiKey: 'sk-1234567890abcdefghijklmnopqrstuvwxyz' },
    });
    
    expect(decision.redactedArgs.apiKey).not.toBe('sk-1234567890abcdefghijklmnopqrstuvwxyz');
  });

  it('should enforce strict mode deny-overrides', () => {
    const policy = {
      version: 1 as const,
      defaultLevel: 'execute' as const,
      defaultDecision: 'allow' as const,
      strict: true,
      rules: [
        {
          id: 'allow-read',
          match: { tool: 'read_file' },
          decision: 'allow' as const,
          reason: 'Allow reads',
        },
        {
          id: 'deny-sensitive',
          match: { tool: 'read_file', args: [{ type: 'path' as const, pattern: '**/.env*' }] },
          decision: 'deny' as const,
          reason: 'Deny sensitive files',
        },
      ],
    };
    
    const guard = createGuard(policy);
    const decision = guard.check({
      agent: 'coder',
      tool: 'read_file',
      args: { path: '.env' },
    });
    
    expect(decision.verdict).toBe('deny');
  });

  it('should provide explain trace', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy, { explain: true });
    
    const decision = guard.check({
      agent: 'coder',
      tool: 'read_file',
      args: { path: 'src/index.ts' },
    });
    
    expect(decision.trace).toBeDefined();
    expect(decision.trace?.steps).toBeDefined();
  });
});
