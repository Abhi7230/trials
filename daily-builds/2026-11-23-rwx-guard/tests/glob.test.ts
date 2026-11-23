import { describe, it, expect } from 'vitest';
import { matchGlob, matchAnyGlob } from '../src/match/glob.js';

describe('glob matching', () => {
  it('should match exact strings', () => {
    expect(matchGlob('foo', 'foo')).toBe(true);
    expect(matchGlob('foo', 'bar')).toBe(false);
  });

  it('should match wildcards', () => {
    expect(matchGlob('*.ts', 'file.ts')).toBe(true);
    expect(matchGlob('*.ts', 'file.js')).toBe(false);
    expect(matchGlob('**/*.ts', 'src/index.ts')).toBe(true);
    expect(matchGlob('**/*.ts', 'src/deep/file.ts')).toBe(true);
  });

  it('should match dotfiles', () => {
    expect(matchGlob('**/.env*', '.env')).toBe(true);
    expect(matchGlob('**/.env*', 'config/.env.local')).toBe(true);
    expect(matchGlob('**/.env*', 'normal.ts')).toBe(false);
  });

  it('should match any glob', () => {
    expect(matchAnyGlob(['*.ts', '*.js'], 'file.ts')).toBe(true);
    expect(matchAnyGlob(['*.ts', '*.js'], 'file.js')).toBe(true);
    expect(matchAnyGlob(['*.ts', '*.js'], 'file.py')).toBe(false);
  });

  it('should handle question mark wildcards', () => {
    expect(matchGlob('file?.ts', 'file1.ts')).toBe(true);
    expect(matchGlob('file?.ts', 'file12.ts')).toBe(false);
  });
});
