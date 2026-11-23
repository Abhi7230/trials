import type { AuditCall } from './parse.js';

export function adaptOpenAI(data: any, agent: string = 'openai'): AuditCall[] {
  const calls: AuditCall[] = [];

  if (Array.isArray(data)) {
    for (const item of data) {
      if (item.tool_calls) {
        for (const toolCall of item.tool_calls) {
          calls.push({
            ts: item.timestamp || Date.now(),
            agent,
            tool: toolCall.function?.name || toolCall.name,
            args: JSON.parse(toolCall.function?.arguments || '{}'),
          });
        }
      }
    }
  } else if (data.tool_calls) {
    for (const toolCall of data.tool_calls) {
      calls.push({
        ts: data.timestamp || Date.now(),
        agent,
        tool: toolCall.function?.name || toolCall.name,
        args: JSON.parse(toolCall.function?.arguments || '{}'),
      });
    }
  }

  return calls;
}

export function adaptAnthropic(data: any, agent: string = 'anthropic'): AuditCall[] {
  const calls: AuditCall[] = [];

  if (Array.isArray(data)) {
    for (const item of data) {
      if (item.content) {
        for (const block of item.content) {
          if (block.type === 'tool_use') {
            calls.push({
              ts: item.timestamp || Date.now(),
              agent,
              tool: block.name,
              args: block.input || {},
            });
          }
        }
      }
    }
  } else if (data.content) {
    for (const block of data.content) {
      if (block.type === 'tool_use') {
        calls.push({
          ts: data.timestamp || Date.now(),
          agent,
          tool: block.name,
          args: block.input || {},
        });
      }
    }
  }

  return calls;
}
