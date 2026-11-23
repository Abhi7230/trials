import { readFileSync } from 'node:fs';
import { parse as parseYaml } from 'yaml';
import { PolicySchema, type Policy } from './schema.js';
import { PolicyValidationError } from '../errors.js';

export function loadPolicy(path: string): Policy {
  const content = readFileSync(path, 'utf-8');
  const isJson = path.endsWith('.json');
  
  let data: unknown;
  try {
    data = isJson ? JSON.parse(content) : parseYaml(content);
  } catch (err) {
    throw new PolicyValidationError(
      `Failed to parse policy file: ${err instanceof Error ? err.message : String(err)}`
    );
  }

  const result = PolicySchema.safeParse(data);
  if (!result.success) {
    const errors = result.error.errors.map((e) => {
      const path = e.path.join('.');
      return `  ${path}: ${e.message}`;
    });
    throw new PolicyValidationError(
      `Invalid policy:\n${errors.join('\n')}`
    );
  }

  return result.data;
}

export function parsePolicy(content: string, format: 'json' | 'yaml'): Policy {
  let data: unknown;
  try {
    data = format === 'json' ? JSON.parse(content) : parseYaml(content);
  } catch (err) {
    throw new PolicyValidationError(
      `Failed to parse policy: ${err instanceof Error ? err.message : String(err)}`
    );
  }

  const result = PolicySchema.safeParse(data);
  if (!result.success) {
    const errors = result.error.errors.map((e) => {
      const path = e.path.join('.');
      return `  ${path}: ${e.message}`;
    });
    throw new PolicyValidationError(
      `Invalid policy:\n${errors.join('\n')}`
    );
  }

  return result.data;
}
