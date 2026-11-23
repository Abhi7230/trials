import { describe, it, expect } from 'vitest';
import { loadPolicy, parsePolicy } from '../src/policy/load.js';
import { lintPolicy } from '../src/policy/lint.js';
import { getPreset } from '../src/policy/presets.js';
import { PolicyValidationError } from '../src/errors.js';

describe('policy loading', () => {
  it('should load valid YAML policy', () => {
    const policy = loadPolicy('fixtures/policy-dev.yaml');
    expect(policy.version).toBe(1);
    expect(policy.defaultLevel).toBe('execute');
  });

  it('should load locked policy', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    expect(policy.version).toBe(1);
    expect(policy.defaultDecision).toBe('deny');
  });

  it('should reject invalid policy', () => {
    expect(() => loadPolicy('fixtures/policy-bad.yaml')).toThrow(PolicyValidationError);
  });

  it('should provide field path in error', () => {
    try {
      loadPolicy('fixtures/policy-bad.yaml');
      expect.fail('Should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(PolicyValidationError);
      if (err instanceof PolicyValidationError) {
        expect(err.message).toContain('defaultLevel');
      }
    }
  });

  it('should parse JSON policy', () => {
    const policy = parsePolicy('{"version":1,"defaultLevel":"read","defaultDecision":"allow"}', 'json');
    expect(policy.version).toBe(1);
  });
});

describe('policy linting', () => {
  it('should pass clean policy', () => {
    const policy = loadPolicy('fixtures/policy-dev.yaml');
    const result = lintPolicy(policy);
    expect(result.passed).toBe(true);
  });

  it('should detect shadowed rules', () => {
    const policy = loadPolicy('fixtures/policy-shadowed.yaml');
    const result = lintPolicy(policy);
    expect(result.passed).toBe(false);
    expect(result.issues.length).toBeGreaterThan(0);
    
    const shadowedIssue = result.issues.find((i) => i.ruleId === 'deny-write');
    expect(shadowedIssue).toBeDefined();
    expect(shadowedIssue?.message).toContain('shadowed');
  });

  it('should warn on missing reasons', () => {
    const policy = parsePolicy(
      '{"version":1,"defaultLevel":"read","defaultDecision":"allow","rules":[{"id":"test","match":{},"decision":"allow","reason":""}]}',
      'json'
    );
    const result = lintPolicy(policy);
    const issue = result.issues.find((i) => i.ruleId === 'test');
    expect(issue).toBeDefined();
    expect(issue?.message).toContain('reason');
  });

  it('should warn on overly broad allows', () => {
    const policy = parsePolicy(
      '{"version":1,"defaultLevel":"read","defaultDecision":"deny","rules":[{"id":"allow-all","match":{"tool":"*"},"decision":"allow","reason":"test"}]}',
      'json'
    );
    const result = lintPolicy(policy);
    const issue = result.issues.find((i) => i.message.includes('overly broad'));
    expect(issue).toBeDefined();
  });
});

describe('presets', () => {
  it('should load readonly preset', () => {
    const policy = getPreset('readonly');
    expect(policy.defaultLevel).toBe('read');
    expect(policy.defaultDecision).toBe('deny');
  });

  it('should load dev preset', () => {
    const policy = getPreset('dev');
    expect(policy.defaultLevel).toBe('execute');
  });

  it('should load locked preset', () => {
    const policy = getPreset('locked');
    expect(policy.defaultDecision).toBe('deny');
  });
});
