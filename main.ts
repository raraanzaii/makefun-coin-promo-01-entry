// GAVEL — entry program for the make.fun bounty "Launch a coin that sells
// make.fun" (makefun-coin-promo-01). Node 22, standard library only.
//
// The coin is the entry; this program has exactly one job: hand the gate the
// record of the launch. It copies LAUNCH.json from the repository root into
// the output directory, where the grader reads it. LAUNCH.json names the
// coin's mint and the signature of the transaction that created it.
//
// In the grader the repository sits at /bot and the output at /output.
// MAKEFUN_BOT_DIR and MAKEFUN_OUTPUT_DIR override both for a local run:
//
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const botDir = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

const source = join(botDir, 'LAUNCH.json');
const target = join(outputDir, 'LAUNCH.json');

if (!existsSync(source)) {
  console.error(`error: LAUNCH.json is missing from the bot directory (${source})`);
  process.exit(1);
}

// Fail loudly on a malformed launch record instead of handing the gate a
// file it can only refuse: LAUNCH.json must be a JSON object whose "mint"
// and "create_signature" fields are both strings. (Whether the values are
// real base58 of the right length is the gate's call, not this program's.)
let launch: unknown;
try {
  launch = JSON.parse(readFileSync(source, 'utf8'));
} catch (err) {
  console.error(`error: LAUNCH.json is not valid JSON: ${(err as Error).message}`);
  process.exit(1);
}
const record = launch as Record<string, unknown> | null;
if (
  record === null ||
  typeof record !== 'object' ||
  typeof record.mint !== 'string' ||
  typeof record.create_signature !== 'string'
) {
  console.error('error: LAUNCH.json must be an object with string "mint" and "create_signature" fields');
  process.exit(1);
}

mkdirSync(outputDir, { recursive: true });
copyFileSync(source, target);
console.log(`copied LAUNCH.json to ${target}`);
