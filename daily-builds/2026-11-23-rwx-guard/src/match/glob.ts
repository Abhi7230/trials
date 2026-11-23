import picomatch from 'picomatch';

export function matchGlob(pattern: string, value: string): boolean {
  const isMatch = picomatch(pattern, {
    dot: true,
    nocase: false,
  });
  return isMatch(value);
}

export function matchAnyGlob(patterns: string[], value: string): boolean {
  return patterns.some((pattern) => matchGlob(pattern, value));
}
