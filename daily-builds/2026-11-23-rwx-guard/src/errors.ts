import type { Decision } from './engine.js';

export class PolicyDeniedError extends Error {
  constructor(
    message: string,
    public readonly decision: Decision,
  ) {
    super(message);
    this.name = 'PolicyDeniedError';
  }
}

export class PolicyValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'PolicyValidationError';
  }
}
