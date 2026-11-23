import { describe, it, expect } from 'vitest';
import { matchPath, normalizePath, isPathInWorkspace } from '../src/match/path.js';

describe('path matching', () => {
  it('should match simple paths', () => {
    expect(matchPath('src/**', 'src/index.ts')).toBe(true);
    expect(matchPath('src/**', 'lib/index.ts')).toBe(false);
  });

  it('should normalize tilde expansion', () => {
    const normalized = normalizePath('~/file.txt');
    expect(normalized).not.toBeNull();
    expect(normalized).not.toContain('~');
  });

  it('should detect path traversal', () => {
    const result = normalizePath('../../etc/passwd', { workspaceRoot: '/home/user/project' });
    expect(result).toBeNull();
  });

  it('should allow safe relative paths', () => {
    const result = normalizePath('src/../src/index.ts', { workspaceRoot: '/home/user/project' });
    expect(result).not.toBeNull();
  });

  it('should normalize paths without blocking', () => {
    expect(normalizePath('.env')).not.toBeNull();
    expect(normalizePath('config/.env.local')).not.toBeNull();
    expect(normalizePath('.ssh/id_rsa')).not.toBeNull();
  });

  it('should check workspace boundaries', () => {
    expect(isPathInWorkspace('/home/user/project/src/file.ts', '/home/user/project')).toBe(true);
    expect(isPathInWorkspace('/etc/passwd', '/home/user/project')).toBe(false);
  });

  it('should match absolute paths', () => {
    const result = matchPath('**', '/etc/passwd');
    expect(result).toBe(true);
  });
});
