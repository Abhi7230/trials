import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'dist/**',
        'tests/**',
        'scripts/**',
        '**/*.config.*',
        '**/types.ts',
      ],
      thresholds: {
        lines: 80,
        statements: 80,
        functions: 75,
        branches: 75,
      },
    },
    testTimeout: 30000,
  },
});
