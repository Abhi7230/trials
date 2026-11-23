export interface CommandMatchResult {
  allowed: boolean;
  reason?: string;
}

export function matchCommand(
  command: string,
  allowBinaries?: string[],
  denyPatterns?: string[]
): CommandMatchResult {
  const tokens = tokenizeCommand(command);
  
  if (tokens.length === 0) {
    return { allowed: true };
  }

  if (denyPatterns && denyPatterns.length > 0) {
    for (const pattern of denyPatterns) {
      if (matchCommandPattern(command, tokens, pattern)) {
        return {
          allowed: false,
          reason: `Command matches deny pattern "${pattern}"`,
        };
      }
    }
  }

  if (allowBinaries && allowBinaries.length > 0) {
    const binary = tokens[0];
    if (!binary) {
      return { allowed: false, reason: 'No binary found in command' };
    }
    
    const baseBinary = binary.split('/').pop() || binary;
    
    if (!allowBinaries.includes(baseBinary)) {
      return {
        allowed: false,
        reason: `Binary "${baseBinary}" is not in allow list`,
      };
    }
  }

  return { allowed: true };
}

function tokenizeCommand(command: string): string[] {
  const tokens: string[] = [];
  let current = '';
  let inSingleQuote = false;
  let inDoubleQuote = false;
  let escaped = false;

  for (let i = 0; i < command.length; i++) {
    const char = command[i];
    if (!char) continue;

    if (escaped) {
      current += char;
      escaped = false;
      continue;
    }

    if (char === '\\') {
      escaped = true;
      continue;
    }

    if (char === "'" && !inDoubleQuote) {
      inSingleQuote = !inSingleQuote;
      continue;
    }

    if (char === '"' && !inSingleQuote) {
      inDoubleQuote = !inDoubleQuote;
      continue;
    }

    if (!inSingleQuote && !inDoubleQuote) {
      if (char === ' ' || char === '\t' || char === '\n') {
        if (current) {
          tokens.push(current);
          current = '';
        }
        continue;
      }

      if (char === ';' || char === '|' || char === '&') {
        if (current) {
          tokens.push(current);
          current = '';
        }
        tokens.push(char);
        continue;
      }
    }

    current += char;
  }

  if (current) {
    tokens.push(current);
  }

  return tokens;
}

function matchCommandPattern(command: string, tokens: string[], pattern: string): boolean {
  const normalizedCommand = command.toLowerCase().replace(/\s+/g, ' ').trim();
  const normalizedPattern = pattern.toLowerCase().replace(/\s+/g, ' ').trim();

  if (normalizedPattern.includes('*')) {
    const regex = new RegExp(
      '^' + normalizedPattern.replace(/\*/g, '.*') + '$'
    );
    return regex.test(normalizedCommand);
  }

  if (normalizedCommand.includes(normalizedPattern)) {
    return true;
  }

  if (tokens.some((t) => t.includes('$(') || t.includes('`'))) {
    if (pattern.includes('$') || pattern.includes('`')) {
      return true;
    }
  }

  if (tokens.includes('|') && pattern.includes('|')) {
    return true;
  }

  if (tokens[0] === 'sudo' && pattern.includes('sudo')) {
    return true;
  }

  return false;
}
