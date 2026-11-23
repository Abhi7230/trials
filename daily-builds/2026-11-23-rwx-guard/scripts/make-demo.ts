import { readFileSync, writeFileSync } from 'node:fs';
import { Resvg } from '@resvg/resvg-js';
import { parseJSONL } from '../src/audit/parse.js';
import { replayCalls, computeStats } from '../src/audit/replay.js';
import { createGuard } from '../src/engine.js';
import { loadPolicy } from '../src/policy/load.js';
import { formatTextReport } from '../src/report/text.js';

function textToSVG(text: string, width: number = 800, lineHeight: number = 20): string {
  const lines = text.split('\n');
  const height = lines.length * lineHeight + 40;
  
  const svgLines = lines.map((line, i) => {
    const escaped = line
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
    return `<text x="20" y="${30 + i * lineHeight}" font-family="monospace" font-size="14" fill="#e0e0e0">${escaped}</text>`;
  });
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="100%" height="100%" fill="#1a1a1a"/>
  ${svgLines.join('\n  ')}
</svg>`;
}

async function main() {
  const policy = loadPolicy('fixtures/policy-locked.yaml');
  const guard = createGuard(policy);
  const content = readFileSync('fixtures/calls-risky.jsonl', 'utf-8');
  const calls = parseJSONL(content);
  
  const result = replayCalls(calls, guard);
  const stats = computeStats(result);
  
  const report = formatTextReport(stats, false);
  
  const svg = textToSVG(report, 1000);
  
  const resvg = new Resvg(svg, {
    fitTo: {
      mode: 'width',
      value: 1000,
    },
  });
  
  const pngData = resvg.render();
  const pngBuffer = pngData.asPng();
  
  writeFileSync('docs/demo.png', pngBuffer);
  
  console.log('Demo image generated at docs/demo.png');
}

main().catch(console.error);
