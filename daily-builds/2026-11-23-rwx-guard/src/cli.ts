#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'node:fs';
import { Command } from 'commander';
import pc from 'picocolors';
import { LEVELS } from './levels.js';
import { loadPolicy, parsePolicy } from './policy/load.js';
import { getPreset } from './policy/presets.js';
import { lintPolicy } from './policy/lint.js';
import { createGuard } from './engine.js';
import { parseJSONL } from './audit/parse.js';
import { adaptOpenAI, adaptAnthropic } from './audit/adapters.js';
import { replayCalls, computeStats } from './audit/replay.js';
import { suggestPolicy, policyToYAML } from './audit/suggest.js';
import { formatTextReport } from './report/text.js';
import { formatJsonReport } from './report/json.js';
import { formatMarkdownReport } from './report/markdown.js';

export function main(argv: string[]): number {
  let exitCode = 0;

  const program = new Command();

  program
    .name('rwx-guard')
    .description('Offline permission-policy engine and auditor for AI-agent tool calls')
    .version('1.0.0')
    .exitOverride((err) => {
      if (err.code === 'commander.help' || err.code === 'commander.version') {
        exitCode = 0;
      } else {
        exitCode = 1;
      }
      throw err;
    });

  program
    .command('check')
    .description('Check a single tool call against a policy')
    .requiredOption('--policy <file>', 'Policy file (YAML or JSON)')
    .requiredOption('--tool <name>', 'Tool name')
    .requiredOption('--args <json>', 'Tool arguments as JSON')
    .option('--agent <name>', 'Agent name', 'default')
    .option('--explain', 'Show decision trace')
    .action((options) => {
      try {
        const policy = loadPolicy(options.policy);
        const args = JSON.parse(options.args);
        const guard = createGuard(policy, { explain: options.explain });
        
        const decision = guard.check({
          agent: options.agent,
          tool: options.tool,
          args,
        });

        console.log(JSON.stringify(decision, null, 2));
        exitCode = decision.verdict === 'deny' ? 1 : 0;
      } catch (err) {
        console.error(pc.red('Error:'), err instanceof Error ? err.message : String(err));
        exitCode = 2;
      }
    });

  program
    .command('audit')
    .description('Audit a log of tool calls against a policy')
    .requiredOption('--policy <file>', 'Policy file (YAML or JSON)')
    .requiredOption('--log <file>', 'Tool call log (JSONL)')
    .option('--format <type>', 'Output format (text|json|markdown)', 'text')
    .option('--fail-on <verdict>', 'Fail if any calls match verdict (denied|ask|none)', 'none')
    .option('--max-denied <n>', 'Maximum allowed denied calls', '999999')
    .option('--suggest <file>', 'Write suggested least-privilege policy to file')
    .action((options) => {
      try {
        const policy = loadPolicy(options.policy);
        const content = readFileSync(options.log, 'utf-8');
        const calls = parseJSONL(content);
        
        const guard = createGuard(policy);
        const result = replayCalls(calls, guard);
        const stats = computeStats(result);

        const useColor = process.stdout.isTTY && options.format === 'text';
        
        let output: string;
        if (options.format === 'json') {
          output = formatJsonReport(stats);
        } else if (options.format === 'markdown') {
          output = formatMarkdownReport(stats);
        } else {
          output = formatTextReport(stats, useColor);
        }

        console.log(output);

        if (options.suggest) {
          const suggested = suggestPolicy(calls);
          const yaml = policyToYAML(suggested);
          writeFileSync(options.suggest, yaml, 'utf-8');
          console.log(`\nSuggested policy written to ${options.suggest}`);
        }

        const maxDenied = parseInt(options.maxDenied, 10);
        if (result.denied > maxDenied) {
          console.error(pc.red(`\nFailed: ${result.denied} denied calls exceeds maximum ${maxDenied}`));
          exitCode = 1;
          return;
        }

        if (options.failOn === 'denied' && result.denied > 0) {
          exitCode = 1;
          return;
        }

        if (options.failOn === 'ask' && result.ask > 0) {
          exitCode = 1;
          return;
        }

        exitCode = 0;
      } catch (err) {
        console.error(pc.red('Error:'), err instanceof Error ? err.message : String(err));
        exitCode = 2;
      }
    });

  program
    .command('lint')
    .description('Lint a policy file')
    .argument('<file>', 'Policy file to lint')
    .option('--format <type>', 'Output format (text|json)', 'text')
    .action((file, options) => {
      try {
        const policy = loadPolicy(file);
        const result = lintPolicy(policy);

        if (options.format === 'json') {
          console.log(JSON.stringify(result, null, 2));
        } else {
          if (result.issues.length === 0) {
            console.log(pc.green('✓ No issues found'));
          } else {
            for (const issue of result.issues) {
              const prefix = issue.severity === 'error' ? pc.red('✗') : pc.yellow('⚠');
              const ruleId = issue.ruleId ? ` (${issue.ruleId})` : '';
              console.log(`${prefix} ${issue.message}${ruleId}`);
            }
          }
        }

        exitCode = result.passed ? 0 : 1;
      } catch (err) {
        console.error(pc.red('Error:'), err instanceof Error ? err.message : String(err));
        exitCode = 2;
      }
    });

  program
    .command('init')
    .description('Generate a new policy file')
    .option('--preset <name>', 'Preset to use (readonly|dev|locked)', 'dev')
    .action((options) => {
      try {
        const preset = options.preset as 'readonly' | 'dev' | 'locked';
        const policy = getPreset(preset);
        const yaml = policyToYAML(policy);
        console.log(yaml);
        exitCode = 0;
      } catch (err) {
        console.error(pc.red('Error:'), err instanceof Error ? err.message : String(err));
        exitCode = 2;
      }
    });

  program
    .command('levels')
    .description('Show available permission levels')
    .action(() => {
      console.log('Permission Levels (least to most permissive):');
      console.log('');
      for (const level of LEVELS) {
        console.log(`  ${level}`);
      }
      exitCode = 0;
    });

  try {
    program.parse(argv);
  } catch (err) {
    // Ignore commander errors, exitCode is already set
  }
  
  return exitCode;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const exitCode = main(process.argv);
  process.exit(exitCode);
}
