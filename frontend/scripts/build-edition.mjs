import { spawnSync } from 'node:child_process';

const allowedEditions = new Set(['full', 'hosting']);
const edition = process.argv[2];

if (!allowedEditions.has(edition)) {
  console.error('Usage: node scripts/build-edition.mjs <full|hosting>');
  process.exit(2);
}

const isWindows = process.platform === 'win32';
const npmCommand = isWindows ? 'npm' : 'npm';
const env = {
  ...process.env,
  VITE_ASTREA_EDITION: edition,
};

if (edition === 'hosting' && process.env.VITE_CANDIDATE_FORM_ENABLED === undefined) {
  // HOSTING stays disabled by default, but an explicit preview/build flag may opt in.
  env.VITE_CANDIDATE_FORM_ENABLED = 'false';
}

console.log(`Building Astrea ${edition.toUpperCase()} edition.`);

const result = spawnSync(npmCommand, ['run', 'build:app'], {
  cwd: process.cwd(),
  env,
  shell: isWindows,
  stdio: 'inherit',
});

if (result.error) {
  throw result.error;
}

process.exit(result.status ?? 1);
