import type { Policy } from './schema.js';

export const PRESET_READONLY: Policy = {
  version: 1,
  defaultLevel: 'read',
  defaultDecision: 'deny',
  strict: true,
  tools: {
    'read_*': { level: 'read' },
    'list_*': { level: 'read' },
    'search_*': { level: 'read' },
    'get_*': { level: 'read' },
  },
  rules: [
    {
      id: 'deny-write',
      match: {},
      decision: 'deny',
      reason: 'Readonly preset denies all write and execute operations',
      level: 'write',
    },
  ],
};

export const PRESET_DEV: Policy = {
  version: 1,
  defaultLevel: 'execute',
  defaultDecision: 'allow',
  strict: false,
  tools: {
    'shell': { level: 'execute' },
    'exec': { level: 'execute' },
    'write_*': { level: 'write' },
    'delete_*': { level: 'write' },
    'read_*': { level: 'read' },
    'list_*': { level: 'read' },
  },
  rules: [
    {
      id: 'deny-dangerous-paths',
      match: {
        args: [
          { type: 'path', pattern: '**/.env*' },
          { type: 'path', pattern: '**/.ssh/*' },
          { type: 'path', pattern: '**/id_rsa*' },
        ],
      },
      decision: 'deny',
      reason: 'Sensitive files are protected',
    },
    {
      id: 'deny-dangerous-commands',
      match: {
        tool: 'shell',
        args: [
          {
            type: 'command',
            denyPatterns: ['rm -rf /', 'curl*|*sh', 'sudo*'],
          },
        ],
      },
      decision: 'deny',
      reason: 'Dangerous commands are blocked',
    },
    {
      id: 'deny-metadata-ip',
      match: {
        args: [
          {
            type: 'host',
            deny: ['169.254.169.254', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'],
          },
        ],
      },
      decision: 'deny',
      reason: 'Internal/metadata IPs are blocked',
    },
  ],
};

export const PRESET_LOCKED: Policy = {
  version: 1,
  defaultLevel: 'zero',
  defaultDecision: 'deny',
  strict: true,
  tools: {
    'read_file': { level: 'read' },
    'list_files': { level: 'read' },
  },
  rules: [
    {
      id: 'allow-read-workspace',
      match: {
        tool: 'read_file',
        args: [{ type: 'path', pattern: 'src/**' }],
      },
      decision: 'allow',
      reason: 'Only reading from src/ is allowed',
    },
  ],
};

export function getPreset(name: 'readonly' | 'dev' | 'locked'): Policy {
  switch (name) {
    case 'readonly':
      return PRESET_READONLY;
    case 'dev':
      return PRESET_DEV;
    case 'locked':
      return PRESET_LOCKED;
  }
}
