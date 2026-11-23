import { z } from 'zod';

export const LevelSchema = z.enum(['zero', 'read', 'write', 'execute']);

export const DecisionSchema = z.enum(['deny', 'ask', 'allow']);

export const ToolDefinitionSchema = z.object({
  level: LevelSchema,
  description: z.string().optional(),
});

export const PathMatcherSchema = z.object({
  type: z.literal('path'),
  pattern: z.string(),
});

export const HostMatcherSchema = z.object({
  type: z.literal('host'),
  allow: z.array(z.string()).optional(),
  deny: z.array(z.string()).optional(),
});

export const CommandMatcherSchema = z.object({
  type: z.literal('command'),
  allowBinaries: z.array(z.string()).optional(),
  denyPatterns: z.array(z.string()).optional(),
});

export const RegexMatcherSchema = z.object({
  type: z.literal('regex'),
  pattern: z.string(),
  field: z.string(),
});

export const NumericMatcherSchema = z.object({
  type: z.literal('numeric'),
  field: z.string(),
  min: z.number().optional(),
  max: z.number().optional(),
});

export const MaxBytesMatcherSchema = z.object({
  type: z.literal('maxBytes'),
  field: z.string(),
  max: z.number(),
});

export const ArgMatcherSchema = z.discriminatedUnion('type', [
  PathMatcherSchema,
  HostMatcherSchema,
  CommandMatcherSchema,
  RegexMatcherSchema,
  NumericMatcherSchema,
  MaxBytesMatcherSchema,
]);

export const RuleMatchSchema = z.object({
  tool: z.string().optional(),
  agent: z.string().optional(),
  args: z.array(ArgMatcherSchema).optional(),
});

export const RuleSchema = z.object({
  id: z.string(),
  match: RuleMatchSchema,
  decision: DecisionSchema,
  reason: z.string(),
  level: LevelSchema.optional(),
});

export const BudgetSchema = z.object({
  tool: z.string(),
  max: z.number().positive(),
  windowSec: z.number().positive(),
});

export const PolicySchema = z.object({
  version: z.literal(1),
  defaultLevel: LevelSchema,
  defaultDecision: DecisionSchema,
  strict: z.boolean().optional().default(false),
  tools: z.record(z.string(), ToolDefinitionSchema).optional(),
  rules: z.array(RuleSchema).optional(),
  budgets: z.array(BudgetSchema).optional(),
});

export type Level = z.infer<typeof LevelSchema>;
export type Decision = z.infer<typeof DecisionSchema>;
export type ToolDefinition = z.infer<typeof ToolDefinitionSchema>;
export type ArgMatcher = z.infer<typeof ArgMatcherSchema>;
export type RuleMatch = z.infer<typeof RuleMatchSchema>;
export type Rule = z.infer<typeof RuleSchema>;
export type Budget = z.infer<typeof BudgetSchema>;
export type Policy = z.infer<typeof PolicySchema>;
