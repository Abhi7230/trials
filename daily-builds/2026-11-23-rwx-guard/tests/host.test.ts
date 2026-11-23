import { describe, it, expect } from 'vitest';
import { matchHost } from '../src/match/host.js';

describe('host matching', () => {
  it('should allow any host by default', () => {
    const result = matchHost('https://example.com');
    expect(result.allowed).toBe(true);
  });

  it('should block userinfo in URLs', () => {
    const result = matchHost('https://user:pass@evil.com');
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('userinfo');
  });

  it('should match exact hostnames', () => {
    const result = matchHost('https://evil.com', undefined, ['evil.com']);
    expect(result.allowed).toBe(false);
  });

  it('should match wildcard domains', () => {
    const result = matchHost('https://sub.evil.com', undefined, ['*.evil.com']);
    expect(result.allowed).toBe(false);
  });

  it('should block metadata IP', () => {
    const result = matchHost('http://169.254.169.254', undefined, ['169.254.169.254']);
    expect(result.allowed).toBe(false);
  });

  it('should block private IPs via CIDR', () => {
    expect(matchHost('http://10.0.0.1', undefined, ['10.0.0.0/8']).allowed).toBe(false);
    expect(matchHost('http://192.168.1.1', undefined, ['192.168.0.0/16']).allowed).toBe(false);
    expect(matchHost('http://172.16.0.1', undefined, ['172.16.0.0/12']).allowed).toBe(false);
  });

  it('should allow hosts in allow list', () => {
    const result = matchHost('https://good.com', ['good.com', 'trusted.com']);
    expect(result.allowed).toBe(true);
  });

  it('should deny hosts not in allow list', () => {
    const result = matchHost('https://evil.com', ['good.com']);
    expect(result.allowed).toBe(false);
  });

  it('should handle localhost', () => {
    const result = matchHost('http://127.0.0.1', undefined, ['127.0.0.1']);
    expect(result.allowed).toBe(false);
  });

  it('should extract hostname from URL', () => {
    const result = matchHost('https://example.com:8080/path?query=1', ['example.com']);
    expect(result.allowed).toBe(true);
  });
});
