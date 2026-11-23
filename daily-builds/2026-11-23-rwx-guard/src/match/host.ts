import { matchGlob } from './glob.js';

export interface HostMatchResult {
  allowed: boolean;
  reason?: string;
}

export function matchHost(
  url: string,
  allowList?: string[],
  denyList?: string[]
): HostMatchResult {
  let hostname: string;
  
  try {
    const parsed = new URL(url);
    
    if (parsed.username || parsed.password) {
      return {
        allowed: false,
        reason: 'URL contains credentials (userinfo) which is blocked',
      };
    }
    
    hostname = parsed.hostname;
  } catch {
    hostname = url;
  }

  if (denyList && denyList.length > 0) {
    for (const pattern of denyList) {
      if (matchHostPattern(hostname, pattern)) {
        return {
          allowed: false,
          reason: `Host "${hostname}" matches deny pattern "${pattern}"`,
        };
      }
    }
  }

  if (allowList && allowList.length > 0) {
    for (const pattern of allowList) {
      if (matchHostPattern(hostname, pattern)) {
        return { allowed: true };
      }
    }
    return {
      allowed: false,
      reason: `Host "${hostname}" does not match any allow pattern`,
    };
  }

  return { allowed: true };
}

function matchHostPattern(hostname: string, pattern: string): boolean {
  if (pattern.includes('/')) {
    return matchCIDR(hostname, pattern);
  }

  if (pattern === hostname) {
    return true;
  }

  if (pattern.startsWith('*.')) {
    const domain = pattern.slice(2);
    return hostname === domain || hostname.endsWith('.' + domain);
  }

  return matchGlob(pattern, hostname);
}

function matchCIDR(hostname: string, cidr: string): boolean {
  const [network, prefixLenStr] = cidr.split('/');
  if (!network || !prefixLenStr) return false;

  const prefixLen = parseInt(prefixLenStr, 10);
  if (isNaN(prefixLen)) return false;

  const hostIP = parseIPv4(hostname);
  const networkIP = parseIPv4(network);

  if (hostIP === null || networkIP === null) {
    return false;
  }

  const mask = (0xffffffff << (32 - prefixLen)) >>> 0;
  return (hostIP & mask) === (networkIP & mask);
}

function parseIPv4(ip: string): number | null {
  const parts = ip.split('.');
  if (parts.length !== 4) return null;

  let result = 0;
  for (let i = 0; i < 4; i++) {
    const part = parts[i];
    if (!part) return null;
    const num = parseInt(part, 10);
    if (isNaN(num) || num < 0 || num > 255) return null;
    result = (result << 8) | num;
  }
  return result >>> 0;
}
