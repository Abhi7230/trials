import { describe, it, expect } from 'vitest';
import { main } from '../src/cli.js';

describe('CLI', () => {
  describe('check command', () => {
    it('should check a tool call', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'check',
        '--policy',
        'fixtures/policy-dev.yaml',
        '--tool',
        'read_file',
        '--args',
        '{"path":"src/index.ts"}',
      ]);
      
      expect(exitCode).toBe(0);
    });

    it('should exit 1 for denied call', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'check',
        '--policy',
        'fixtures/policy-locked.yaml',
        '--tool',
        'shell',
        '--args',
        '{"command":"rm -rf /"}',
      ]);
      
      expect(exitCode).toBe(1);
    });
  });

  describe('init command', () => {
    it('should output a policy', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'init',
        '--preset',
        'dev',
      ]);
      
      expect(exitCode).toBe(0);
    });
  });

  describe('levels command', () => {
    it('should show levels', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'levels',
      ]);
      
      expect(exitCode).toBe(0);
    });
  });
});
