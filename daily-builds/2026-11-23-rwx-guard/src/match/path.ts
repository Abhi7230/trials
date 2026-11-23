import { resolve, normalize, isAbsolute } from 'node:path';
import { homedir } from 'node:os';
import { matchGlob } from './glob.js';

export interface PathMatchOptions {
  workspaceRoot?: string;
}

export function matchPath(
  pattern: string,
  path: string,
  options: PathMatchOptions = {}
): boolean {
  const normalizedPath = normalizePath(path, options);
  
  if (normalizedPath === null) {
    return false;
  }

  return matchGlob(pattern, normalizedPath);
}

export function normalizePath(path: string, options: PathMatchOptions = {}): string | null {
  let expanded = path;

  if (expanded.startsWith('~/')) {
    expanded = homedir() + expanded.slice(1);
  }

  expanded = normalize(expanded);

  if (expanded.includes('/../') || expanded.endsWith('/..')) {
    const resolved = resolve(expanded);
    if (options.workspaceRoot) {
      const isInside = isPathInWorkspace(resolved, options.workspaceRoot);
      if (!isInside) {
        return null;
      }
    }
    expanded = resolved;
  }

  return expanded;
}

export function isPathInWorkspace(path: string, workspaceRoot: string): boolean {
  const normalizedPath = isAbsolute(path) ? path : resolve(workspaceRoot, path);
  const normalizedRoot = resolve(workspaceRoot);
  
  return normalizedPath.startsWith(normalizedRoot);
}
