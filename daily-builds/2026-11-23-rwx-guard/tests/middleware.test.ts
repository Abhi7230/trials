import { describe, it, expect } from 'vitest';
import { guardTool, withGuard } from '../src/middleware.js';
import { createGuard } from '../src/engine.js';
import { getPreset } from '../src/policy/presets.js';
import { PolicyDeniedError } from '../src/errors.js';

describe('middleware', () => {
  it('should allow permitted tool calls', () => {
    const policy = getPreset('dev');
    const guard = createGuard(policy);
    
    const readFile = (args: { path: string }) => `content of ${args.path}`;
    const guarded = guardTool(readFile, guard, { agent: 'coder', tool: 'read_file' });
    
    const result = guarded({ path: 'src/index.ts' });
    expect(result).toBe('content of src/index.ts');
  });

  it('should throw on denied calls', () => {
    const policy = getPreset('locked');
    const guard = createGuard(policy);
    
    const shell = (args: { command: string }) => 'executed';
    const guarded = guardTool(shell, guard, { agent: 'coder', tool: 'shell' });
    
    expect(() => guarded({ command: 'ls' })).toThrow(PolicyDeniedError);
  });

  it('should attach decision to error', () => {
    const policy = getPreset('locked');
    const guard = createGuard(policy);
    
    const shell = (args: { command: string }) => 'executed';
    const guarded = guardTool(shell, guard, { agent: 'coder', tool: 'shell' });
    
    try {
      guarded({ command: 'rm -rf /' });
      expect.fail('Should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(PolicyDeniedError);
      if (err instanceof PolicyDeniedError) {
        expect(err.decision).toBeDefined();
        expect(err.decision.verdict).toBe('deny');
      }
    }
  });

  it('should call onAsk handler', () => {
    const policy = {
      version: 1 as const,
      defaultLevel: 'read' as const,
      defaultDecision: 'ask' as const,
    };
    const guard = createGuard(policy);
    
    let askCalled = false;
    const onAsk = () => { askCalled = true; };
    
    const readFile = (args: { path: string }) => 'content';
    const guarded = guardTool(readFile, guard, { agent: 'coder', tool: 'read_file' }, { onAsk });
    
    expect(() => guarded({ path: 'file.ts' })).toThrow(PolicyDeniedError);
    expect(askCalled).toBe(true);
  });

  it('should wrap multiple tools', () => {
    const policy = getPreset('dev');
    const guard = createGuard(policy);
    
    const tools = {
      read_file: (args: { path: string }) => `read ${args.path}`,
      write_file: (args: { path: string; content: string }) => `wrote ${args.content}`,
    };
    
    const wrapped = withGuard(tools, guard, { agent: 'coder' });
    
    expect(wrapped.read_file({ path: 'file.ts' })).toBe('read file.ts');
    expect(wrapped.write_file({ path: 'file.ts', content: 'hello' })).toBe('wrote hello');
  });
});
