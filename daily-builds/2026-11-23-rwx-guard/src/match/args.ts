import type { ArgMatcher } from '../policy/schema.js';
import { matchPath, type PathMatchOptions } from './path.js';
import { matchHost } from './host.js';
import { matchCommand } from './command.js';

export interface ArgsMatchResult {
  matched: boolean;
  reason?: string;
}

export function matchArgs(
  args: Record<string, unknown>,
  matchers: ArgMatcher[],
  options: PathMatchOptions = {}
): ArgsMatchResult {
  for (const matcher of matchers) {
    const result = matchSingleArg(args, matcher, options);
    if (result.matched) {
      return result;
    }
  }

  return { matched: false };
}

function matchSingleArg(
  args: Record<string, unknown>,
  matcher: ArgMatcher,
  options: PathMatchOptions
): ArgsMatchResult {
  switch (matcher.type) {
    case 'path': {
      const pathFields = ['path', 'file', 'filename', 'filepath'];
      for (const field of pathFields) {
        const value = args[field];
        if (typeof value === 'string') {
          if (matchPath(matcher.pattern, value, options)) {
            return {
              matched: true,
              reason: `Path "${value}" matches pattern "${matcher.pattern}"`,
            };
          }
        }
      }
      return { matched: false };
    }

    case 'host': {
      const hostFields = ['url', 'host', 'hostname', 'endpoint'];
      for (const field of hostFields) {
        const value = args[field];
        if (typeof value === 'string') {
          const result = matchHost(value, matcher.allow, matcher.deny);
          if (!result.allowed) {
            return { matched: true, reason: result.reason };
          }
        }
      }
      return { matched: false };
    }

    case 'command': {
      const commandFields = ['command', 'cmd', 'shell', 'exec'];
      for (const field of commandFields) {
        const value = args[field];
        if (typeof value === 'string') {
          const result = matchCommand(value, matcher.allowBinaries, matcher.denyPatterns);
          if (!result.allowed) {
            return { matched: true, reason: result.reason };
          }
        }
      }
      return { matched: false };
    }

    case 'regex': {
      const value = args[matcher.field];
      if (typeof value === 'string') {
        const regex = new RegExp(matcher.pattern);
        if (regex.test(value)) {
          return {
            matched: true,
            reason: `Field "${matcher.field}" matches regex "${matcher.pattern}"`,
          };
        }
      }
      return { matched: false };
    }

    case 'numeric': {
      const value = args[matcher.field];
      if (typeof value === 'number') {
        if (matcher.min !== undefined && value < matcher.min) {
          return {
            matched: true,
            reason: `Field "${matcher.field}" (${value}) is below minimum ${matcher.min}`,
          };
        }
        if (matcher.max !== undefined && value > matcher.max) {
          return {
            matched: true,
            reason: `Field "${matcher.field}" (${value}) exceeds maximum ${matcher.max}`,
          };
        }
      }
      return { matched: false };
    }

    case 'maxBytes': {
      const value = args[matcher.field];
      if (typeof value === 'string') {
        const bytes = Buffer.byteLength(value, 'utf-8');
        if (bytes > matcher.max) {
          return {
            matched: true,
            reason: `Field "${matcher.field}" size (${bytes} bytes) exceeds maximum ${matcher.max} bytes`,
          };
        }
      }
      return { matched: false };
    }
  }
}
