// 生成 web/config.js：把配置项从环境变量注入为 window.__MSPT_ENV__，
// 供 index.html 在构建产物中读取（Vercel / 其他静态托管平台的标准做法）。
// 用法：node web/build-config.mjs
// 优先读取进程环境变量（Vercel 项目环境变量 / CLI vercel env pull）；
// 若进程环境中没有任何配置项，则回退读取 web/.env（key=value 格式）。
// 值均为明文，与 web/.env 中的格式完全一致，可直接在 Vercel 环境变量中原样填写。
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const KEYS = [
  'ACCESS_CODE_HASH', 'SYNC_TARGETS', 'DEFAULT_SOURCE', 'PHRASE_FORMAT',
  'S3_ENDPOINT_URL', 'S3_REGION', 'AWS_REGION',
  'S3_BUCKET', 'S3_BUCKET_NAME', 'S3_PATH', 'S3_DIRECTORY',
  'S3_FILENAME', 'S3_PUBLIC_URL',
  'S3_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID',
  'S3_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY',
  'GITHUB_REPO', 'GITHUB_BRANCH', 'GITHUB_PATH', 'GITHUB_FILENAME', 'GITHUB_TOKEN',
];

function parseEnvText(text){
  const kv = {};
  for(let line of text.split(/\r?\n/)){
    line = line.trim();
    if(!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if(eq < 0) continue;
    let v = line.slice(eq + 1).trim();
    v = v.replace(/\s+#.*$/, '').trim();
    if((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'")))
      v = v.slice(1, -1);
    kv[line.slice(0, eq).trim()] = v;
  }
  return kv;
}

const webDir = dirname(fileURLToPath(import.meta.url));
const kv = {};
for(const k of KEYS){
  const v = process.env[k];
  if(v && v.trim()) kv[k] = v.trim();
}
if(!Object.keys(kv).length){
  const envPath = join(webDir, '.env');
  if(existsSync(envPath)){
    const parsed = parseEnvText(readFileSync(envPath, 'utf8'));
    for(const k of KEYS) if(parsed[k]) kv[k] = parsed[k];
  }
  console.log('[build-config] 进程环境中无配置项，已回退读取 web/.env');
}
writeFileSync(join(webDir, 'config.js'),
  '/* 由 web/build-config.mjs 生成，请勿手工编辑 */\n' +
  'window.__MSPT_ENV__=' + JSON.stringify(kv) + ';\n');
console.log(`[build-config] 已写入 web/config.js（${Object.keys(kv).length} 个配置项）`);
