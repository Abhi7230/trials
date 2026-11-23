import { describe, it, expect } from 'vitest';
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { parseJSONL } from '../src/audit/parse.js';
import { replayCalls } from '../src/audit/replay.js';
import { createGuard } from '../src/engine.js';
import { loadPolicy } from '../src/policy/load.js';
import { lintPolicy } from '../src/policy/lint.js';
import { main } from '../src/cli.js';

describe('integration tests', () => {
  describe('risky calls with locked policy - table-driven', () => {
    const expectedVerdicts = [
      { idx: 0, verdict: 'deny', ruleId: 'deny-env-files' },
      { idx: 1, verdict: 'deny', ruleId: 'deny-env-files' },
      { idx: 2, verdict: 'deny', ruleId: 'deny-ssh-keys' },
      { idx: 3, verdict: 'deny', ruleId: 'deny-ssh-keys' },
      { idx: 4, verdict: 'deny', ruleId: undefined },
      { idx: 5, verdict: 'deny', ruleId: 'deny-rm-rf' },
      { idx: 6, verdict: 'deny', ruleId: 'deny-curl-pipe' },
      { idx: 7, verdict: 'deny', ruleId: 'deny-sudo' },
      { idx: 8, verdict: 'deny', ruleId: 'deny-rm-rf' },
      { idx: 9, verdict: 'deny', ruleId: 'deny-metadata-service' },
      { idx: 10, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 11, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 12, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 13, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 14, verdict: 'deny', ruleId: 'deny-credentials-url' },
      { idx: 15, verdict: 'deny', ruleId: undefined },
      { idx: 16, verdict: 'deny', ruleId: undefined },
      { idx: 17, verdict: 'deny', ruleId: 'deny-curl-pipe' },
      { idx: 18, verdict: 'deny', ruleId: 'deny-curl-pipe' },
      { idx: 19, verdict: 'deny', ruleId: 'deny-env-files' },
      { idx: 20, verdict: 'deny', ruleId: 'deny-private-keys' },
      { idx: 21, verdict: 'deny', ruleId: 'deny-sudo' },
      { idx: 22, verdict: 'deny', ruleId: 'deny-rm-rf' },
      { idx: 23, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 24, verdict: 'deny', ruleId: 'deny-env-files' },
      { idx: 25, verdict: 'deny', ruleId: 'deny-curl-pipe' },
      { idx: 26, verdict: 'deny', ruleId: 'deny-env-files' },
      { idx: 27, verdict: 'deny', ruleId: undefined },
      { idx: 28, verdict: 'deny', ruleId: 'deny-curl-pipe' },
      { idx: 29, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 30, verdict: 'allow', ruleId: 'allow-read-src' },
      { idx: 31, verdict: 'deny', ruleId: 'deny-env-files' },
      { idx: 32, verdict: 'deny', ruleId: 'deny-sudo' },
      { idx: 33, verdict: 'deny', ruleId: 'deny-credentials-url' },
      { idx: 34, verdict: 'deny', ruleId: 'deny-private-keys' },
      { idx: 35, verdict: 'deny', ruleId: 'deny-rm-rf' },
      { idx: 36, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 37, verdict: 'deny', ruleId: 'deny-env-files' },
      { idx: 38, verdict: 'deny', ruleId: 'deny-curl-pipe' },
      { idx: 39, verdict: 'deny', ruleId: 'deny-private-ips' },
      { idx: 40, verdict: 'deny', ruleId: undefined },
      { idx: 41, verdict: 'allow', ruleId: 'allow-list-src' },
      { idx: 42, verdict: 'deny', ruleId: 'deny-sudo' },
    ];

    it.each(expectedVerdicts)(
      'call $idx should have verdict=$verdict ruleId=$ruleId',
      ({ idx, verdict, ruleId }) => {
        const policy = loadPolicy('fixtures/policy-locked.yaml');
        const guard = createGuard(policy);
        const content = readFileSync('fixtures/calls-risky.jsonl', 'utf-8');
        const calls = parseJSONL(content);
        
        const call = calls[idx];
        expect(call).toBeDefined();
        
        const decision = guard.check({
          agent: call!.agent,
          tool: call!.tool,
          args: call!.args,
        });
        
        expect(decision.verdict, `Call ${idx} verdict mismatch`).toBe(verdict);
        expect(decision.ruleId, `Call ${idx} ruleId mismatch`).toBe(ruleId);
      }
    );
  });

  describe('good calls with dev policy', () => {
    it('should allow all good calls', () => {
      const policy = loadPolicy('fixtures/policy-dev.yaml');
      const guard = createGuard(policy);
      const content = readFileSync('fixtures/calls-good.jsonl', 'utf-8');
      const calls = parseJSONL(content);
      
      const result = replayCalls(calls, guard);
      
      expect(result.denied).toBe(0);
      expect(result.allowed).toBe(calls.length);
    });
  });

  describe('CLI audit', () => {
    it('should exit 1 when risky calls are denied with --fail-on denied', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'audit',
        '--policy',
        'fixtures/policy-locked.yaml',
        '--log',
        'fixtures/calls-risky.jsonl',
        '--fail-on',
        'denied',
      ]);
      
      expect(exitCode).toBe(1);
    });

    it('should exit 0 when good calls pass', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'audit',
        '--policy',
        'fixtures/policy-dev.yaml',
        '--log',
        'fixtures/calls-good.jsonl',
        '--fail-on',
        'denied',
      ]);
      
      expect(exitCode).toBe(0);
    });

    it('should respect --max-denied boundary (41 passes, 40 fails)', () => {
      const passCode = main([
        'node',
        'cli.js',
        'audit',
        '--policy',
        'fixtures/policy-locked.yaml',
        '--log',
        'fixtures/calls-risky.jsonl',
        '--max-denied',
        '41',
      ]);
      
      expect(passCode).toBe(0);

      const failCode = main([
        'node',
        'cli.js',
        'audit',
        '--policy',
        'fixtures/policy-locked.yaml',
        '--log',
        'fixtures/calls-risky.jsonl',
        '--max-denied',
        '40',
      ]);
      
      expect(failCode).toBe(1);
    });

    it('should generate suggested policy from good calls', () => {
      const tmpFile = 'fixtures/suggested-good.yaml';
      
      try {
        const exitCode = main([
          'node',
          'cli.js',
          'audit',
          '--policy',
          'fixtures/policy-dev.yaml',
          '--log',
          'fixtures/calls-good.jsonl',
          '--suggest',
          tmpFile,
        ]);
        
        expect(exitCode).toBe(0);
        const suggested = loadPolicy(tmpFile);
        expect(suggested.version).toBe(1);
        
        const guard = createGuard(suggested);
        const content = readFileSync('fixtures/calls-good.jsonl', 'utf-8');
        const calls = parseJSONL(content);
        const result = replayCalls(calls, guard);
        
        expect(result.allowed).toBe(calls.length);
        
        const unseenDecision = guard.check({
          agent: 'test',
          tool: 'unseen_tool',
          args: {},
        });
        expect(unseenDecision.verdict).toBe('deny');
      } finally {
        try {
          unlinkSync(tmpFile);
        } catch {}
      }
    });

    it('should generate suggested policy from risky calls', () => {
      const tmpFile = 'fixtures/suggested-risky.yaml';
      
      try {
        const exitCode = main([
          'node',
          'cli.js',
          'audit',
          '--policy',
          'fixtures/policy-locked.yaml',
          '--log',
          'fixtures/calls-risky.jsonl',
          '--suggest',
          tmpFile,
        ]);
        
        const suggested = loadPolicy(tmpFile);
        expect(suggested.version).toBe(1);
        
        const guard = createGuard(suggested);
        const content = readFileSync('fixtures/calls-risky.jsonl', 'utf-8');
        const calls = parseJSONL(content);
        const result = replayCalls(calls, guard);
        
        expect(result.allowed).toBe(calls.length);
        
        const unseenDecision = guard.check({
          agent: 'test',
          tool: 'unseen_dangerous_tool',
          args: {},
        });
        expect(unseenDecision.verdict).toBe('deny');
      } finally {
        try {
          unlinkSync(tmpFile);
        } catch {}
      }
    });
  });

  describe('CLI lint', () => {
    it('should exit 0 for clean policy', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'lint',
        'fixtures/policy-dev.yaml',
      ]);
      
      expect(exitCode).toBe(0);
    });

    it('should exit 1 and report shadowed rule id deny-write', () => {
      const policy = loadPolicy('fixtures/policy-shadowed.yaml');
      const result = lintPolicy(policy);
      
      expect(result.passed).toBe(false);
      
      const shadowedIssue = result.issues.find((i) => i.ruleId === 'deny-write');
      expect(shadowedIssue).toBeDefined();
      expect(shadowedIssue!.message).toContain('shadowed');
      expect(shadowedIssue!.message).toContain('allow-all');

      const exitCode = main([
        'node',
        'cli.js',
        'lint',
        'fixtures/policy-shadowed.yaml',
      ]);
      
      expect(exitCode).toBe(1);
    });

    it('should exit 2 for malformed policy and name the field', () => {
      const exitCode = main([
        'node',
        'cli.js',
        'lint',
        'fixtures/policy-bad.yaml',
      ]);
      
      expect(exitCode).toBe(2);
    });

    it('should report field name in validation error', () => {
      try {
        loadPolicy('fixtures/policy-bad.yaml');
        expect.fail('Should have thrown');
      } catch (err: any) {
        expect(err.message).toContain('defaultLevel');
        expect(err.message).toContain('Invalid enum value');
      }
    });
  });

  describe('JSON output stability', () => {
    it('should produce byte-stable JSON across runs', () => {
      const policy = loadPolicy('fixtures/policy-locked.yaml');
      const guard = createGuard(policy);
      const content = readFileSync('fixtures/calls-risky.jsonl', 'utf-8');
      const calls = parseJSONL(content);
      
      const result1 = replayCalls(calls, guard);
      const result2 = replayCalls(calls, guard);
      
      const json1 = JSON.stringify(result1, null, 2);
      const json2 = JSON.stringify(result2, null, 2);
      
      expect(json1).toBe(json2);
    });
  });
});
