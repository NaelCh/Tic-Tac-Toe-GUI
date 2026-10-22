import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const source = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(source);
const target = path.join(root, 'dist-mobile');
const files = ['index.html', 'style.css', 'app.js', 'engine.js', 'manifest.webmanifest', 'sw.js'];
const sounds = ['click', 'move_x', 'move_o', 'win', 'lose', 'draw'];
const hash = createHash('sha256');
for (const name of files) hash.update(await readFile(path.join(source, name)));
for (const name of ['icon-192.png', 'icon-512.png', 'apple-touch-icon.png']) {
  hash.update(await readFile(path.join(source, 'icons', name)));
}
for (const name of sounds) hash.update(await readFile(path.join(root, 'assets/sounds', name+'.wav')));
const version = hash.digest('hex').slice(0, 16);
const commit = process.env.GITHUB_SHA || execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim();
await rm(target, {recursive: true, force: true});
await mkdir(target, {recursive: true});
for (const name of files) {
  const content = (await readFile(path.join(source, name), 'utf8')).replace('__CACHE_VERSION__', version);
  await writeFile(path.join(target, name), content);
}
await cp(path.join(source, 'icons'), path.join(target, 'icons'), {recursive: true});
await mkdir(path.join(target, 'sounds'));
for (const name of sounds) await cp(path.join(root, 'assets/sounds', name+'.wav'), path.join(target, 'sounds', name+'.wav'));
await cp(path.join(root, 'THIRD_PARTY.md'), path.join(target, 'THIRD_PARTY.md'));
await writeFile(path.join(target, 'build.json'), JSON.stringify({commit, version})+'\n');
console.log(`Built mobile app ${version} in ${target}`);
