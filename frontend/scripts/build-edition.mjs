import { spawnSync } from 'node:child_process';

const allowedEditions = new Set(['full', 'hosting']);
const edition = process.argv[2];

if (!allowedEditions.has(edition)) {
  console.error('Usage: node scripts/build-edition.mjs <full|hosting>');
  process.exit(2);
}

const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const env = {
  ...process.env,
  VITE_ASTREA_EDITION: edition,
};

if (edition === 'hosting') {
  // Candidate intake is deliberately outside the approved HOSTING MVP.
  env.VITE_CANDIDATE_FORM_ENABLED = 'false';
}

console.log(`Building Astrea ${edition.toUpperCase()} edition.`);

const result = spawnSync(npmCommand, ['run', 'build:app'], {
  cwd: process.cwd(),
  env,
  stdio: 'inherit',
});

if (result.error) {
  throw result.error;
}

process.exit(result.status ?? 1);
