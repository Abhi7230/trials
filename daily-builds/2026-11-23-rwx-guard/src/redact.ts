const SECRET_PATTERNS = [
  /\b(sk-[a-zA-Z0-9]{20,})\b/g,
  /\b(Bearer\s+[a-zA-Z0-9_\-\.]+)\b/gi,
  /\b([a-zA-Z0-9_\-]{32,})\b/g,
  /\b(ghp_[a-zA-Z0-9]{36})\b/g,
  /\b(gho_[a-zA-Z0-9]{36})\b/g,
];

export function redactSecrets(args: Record<string, unknown>): Record<string, unknown> {
  const redacted: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(args)) {
    if (typeof value === 'string') {
      redacted[key] = redactString(value);
    } else if (typeof value === 'object' && value !== null) {
      redacted[key] = redactSecrets(value as Record<string, unknown>);
    } else {
      redacted[key] = value;
    }
  }

  return redacted;
}

function redactString(str: string): string {
  let result = str;
  
  for (const pattern of SECRET_PATTERNS) {
    result = result.replace(pattern, (match) => {
      if (match.length <= 8) return match;
      return match.slice(0, 4) + '***' + match.slice(-4);
    });
  }

  return result;
}
