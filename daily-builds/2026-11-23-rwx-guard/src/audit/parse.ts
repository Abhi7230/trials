export interface AuditCall {
  ts: number;
  agent: string;
  tool: string;
  args: Record<string, unknown>;
}

export function parseJSONL(content: string): AuditCall[] {
  const lines = content.split('\n').filter((line) => line.trim());
  const calls: AuditCall[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line) continue;

    try {
      const parsed = JSON.parse(line);
      calls.push({
        ts: parsed.ts || Date.now(),
        agent: parsed.agent || 'unknown',
        tool: parsed.tool,
        args: parsed.args || {},
      });
    } catch (err) {
      throw new Error(`Failed to parse line ${i + 1}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return calls;
}
