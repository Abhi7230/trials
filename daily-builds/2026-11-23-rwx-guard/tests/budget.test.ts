import { describe, it, expect } from 'vitest';
import { createBudgetTracker } from '../src/budget.js';

describe('budget tracker', () => {
  it('should allow calls within budget', () => {
    const tracker = createBudgetTracker([
      { tool: 'read_file', max: 5, windowSec: 60 },
    ]);
    
    const result = tracker.check('read_file', 'coder', 1000);
    expect(result.allowed).toBe(true);
  });

  it('should deny calls exceeding budget', () => {
    const tracker = createBudgetTracker([
      { tool: 'read_file', max: 2, windowSec: 60 },
    ]);
    
    tracker.record('read_file', 'coder', 1000);
    tracker.record('read_file', 'coder', 2000);
    
    const result = tracker.check('read_file', 'coder', 3000);
    expect(result.allowed).toBe(false);
  });

  it('should use sliding window', () => {
    const tracker = createBudgetTracker([
      { tool: 'read_file', max: 2, windowSec: 10 },
    ]);
    
    tracker.record('read_file', 'coder', 1000);
    tracker.record('read_file', 'coder', 2000);
    
    const result1 = tracker.check('read_file', 'coder', 3000);
    expect(result1.allowed).toBe(false);
    
    const result2 = tracker.check('read_file', 'coder', 15000);
    expect(result2.allowed).toBe(true);
  });

  it('should track per agent', () => {
    const tracker = createBudgetTracker([
      { tool: 'read_file', max: 2, windowSec: 60 },
    ]);
    
    tracker.record('read_file', 'coder1', 1000);
    tracker.record('read_file', 'coder1', 2000);
    
    const result = tracker.check('read_file', 'coder2', 3000);
    expect(result.allowed).toBe(true);
  });

  it('should handle wildcard tools', () => {
    const tracker = createBudgetTracker([
      { tool: '*', max: 3, windowSec: 60 },
    ]);
    
    tracker.record('read_file', 'coder', 1000);
    tracker.record('write_file', 'coder', 2000);
    tracker.record('delete_file', 'coder', 3000);
    
    const result = tracker.check('shell', 'coder', 4000);
    expect(result.allowed).toBe(false);
  });
});
