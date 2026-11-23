import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { parseJSONL } from '../src/audit/parse.js';
import { adaptOpenAI, adaptAnthropic } from '../src/audit/adapters.js';
import { replayCalls, computeStats } from '../src/audit/replay.js';
import { suggestPolicy, policyToYAML } from '../src/audit/suggest.js';
import { createGuard } from '../src/engine.js';
import { loadPolicy } from '../src/policy/load.js';

describe('audit parsing', () => {
  it('should parse JSONL format', () => {
    const content = readFileSync('fixtures/calls-good.jsonl', 'utf-8');
    const calls = parseJSONL(content);
    expect(calls.length).toBeGreaterThan(0);
    expect(calls[0]?.tool).toBeDefined();
  });

  it('should handle empty lines', () => {
    const content = '{"ts":1000,"agent":"a","tool":"t","args":{}}\n\n{"ts":2000,"agent":"b","tool":"t2","args":{}}';
    const calls = parseJSONL(content);
    expect(calls.length).toBe(2);
  });
});

describe('audit adapters', () => {
  it('should adapt OpenAI format', () => {
    const content = readFileSync('fixtures/openai-calls.json', 'utf-8');
    const data = JSON.parse(content);
    const calls = adaptOpenAI(data);
    expect(calls.length).toBe(2);
    expect(calls[0]?.tool).toBe('read_file');
  });

  it('should adapt Anthropic format', () => {
    const content = readFileSync('fixtures/anthropic-calls.json', 'utf-8');
    const data = JSON.parse(content);
    const calls = adaptAnthropic(data);
    expect(calls.length).toBe(2);
    expect(calls[0]?.tool).toBe('read_file');
  });
});

describe('audit replay', () => {
  it('should replay calls against policy', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy);
    const content = readFileSync('fixtures/calls-good.jsonl', 'utf-8');
    const calls = parseJSONL(content);
    
    const result = replayCalls(calls, guard);
    expect(result.total).toBe(calls.length);
    expect(result.allowed + result.denied + result.ask).toBe(result.total);
  });

  it('should compute statistics', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy);
    const content = readFileSync('fixtures/calls-risky.jsonl', 'utf-8');
    const calls = parseJSONL(content);
    
    const result = replayCalls(calls, guard);
    const stats = computeStats(result);
    
    expect(stats.total).toBe(calls.length);
    expect(stats.byVerdict['deny']).toBeGreaterThan(0);
  });

  it('should identify top denied rules', () => {
    const policy = loadPolicy('fixtures/policy-locked.yaml');
    const guard = createGuard(policy);
    const content = readFileSync('fixtures/calls-risky.jsonl', 'utf-8');
    const calls = parseJSONL(content);
    
    const result = replayCalls(calls, guard);
    const stats = computeStats(result);
    
    expect(stats.topDeniedRules.length).toBeGreaterThan(0);
    expect(stats.topDeniedRules[0]?.count).toBeGreaterThan(0);
  });
});

describe('policy suggestion', () => {
  it('should generate least-privilege policy', () => {
    const content = readFileSync('fixtures/calls-good.jsonl', 'utf-8');
    const calls = parseJSONL(content);
    
    const policy = suggestPolicy(calls);
    expect(policy.version).toBe(1);
    expect(policy.defaultDecision).toBe('deny');
    expect(policy.tools).toBeDefined();
  });

  it('should convert policy to YAML', () => {
    const content = readFileSync('fixtures/calls-good.jsonl', 'utf-8');
    const calls = parseJSONL(content);
    
    const policy = suggestPolicy(calls);
    const yaml = policyToYAML(policy);
    
    expect(yaml).toContain('version:');
    expect(yaml).toContain('defaultDecision:');
  });

  it('should allow observed tools and deny unseen', () => {
    const calls = parseJSONL('{"ts":1000,"agent":"a","tool":"read_file","args":{}}');
    const policy = suggestPolicy(calls);
    
    const guard = createGuard(policy);
    
    const readDecision = guard.check({
      agent: 'a',
      tool: 'read_file',
      args: {},
    });
    expect(readDecision.verdict).toBe('allow');
    
    const writeDecision = guard.check({
      agent: 'a',
      tool: 'write_file',
      args: {},
    });
    expect(writeDecision.verdict).toBe('deny');
  });
});
