# SMART Analyzer – Schema→Codegen→Supabase Kit

A pre-wired, **real data only** pipeline you can drop into the repo to enumerate content from APIs, generate typed clients, and persist results in Supabase with provenance.

> Modes supported: **Sitecore GraphQL (preferred)** • **OpenAPI** • **Sitemaps** • **JSON sample → types** • **Sitecore SSC/SPE/SCS uploads**

---

## 0) Prereqs
- Node 18+
- pnpm (or npm)
- Supabase project (URL + service key)
- For Sitecore: GraphQL endpoint + API key (e.g., `https://<host>/sitecore/api/graph/edge`, header: `sc_apikey`)

### .env (root)
```bash
# Supabase
SUPABASE_URL="https://xxx.supabase.co"
SUPABASE_SERVICE_ROLE="<service key>"

# Sitecore
SC_ENDPOINT="https://<host>/sitecore/api/graph/edge"
SC_API_KEY="<your sitecore api key>"

# Optional: Google PSI (if you also run perf analyzer)
PSI_API_KEY="<google pagespeed key>"
```

---

## 1) Workspace layout (drop-in)
```
/packages
  /core                 # types, errors, utils
  /db                   # supabase client + helpers (single door to DB)
  /extractors           # codegen outputs + enumerators (graphql/openapi/sitemap/json)
  /ingest               # normalize & persist routines (shared)
```

Add to root `package.json`:
```json
{
  "workspaces": ["packages/*"],
  "scripts": {
    "gql:schema": "get-graphql-schema $SC_ENDPOINT -h 'Content-Type: application/json' -h 'sc_apikey: ' \"$SC_API_KEY\" > packages/extractors/sitecore/schema.graphql",
    "gql:codegen": "graphql-codegen --config packages/extractors/sitecore/codegen.yml",
    "enumerate:sitecore": "ts-node packages/extractors/sitecore/enumerate.ts",
    "enumerate:openapi": "openapi-typescript $OPENAPI_URL -o packages/extractors/openapi/types.d.ts && ts-node packages/extractors/openapi/enumerate.ts",
    "enumerate:sitemap": "ts-node packages/extractors/sitemap/enumerate.ts",
    "types:quick": "quicktype -s json packages/extractors/json/samples/*.json -o packages/extractors/json/types.ts"
  },
  "devDependencies": {
    "@graphql-codegen/cli": "^5",
    "@graphql-codegen/typescript": "^4",
    "@graphql-codegen/typescript-operations": "^4",
    "@graphql-codegen/typescript-graphql-request": "^6",
    "graphql": "^16",
    "get-graphql-schema": "^2",
    "graphql-request": "^7",
    "openapi-typescript": "^7",
    "quicktype": "^23",
    "ts-node": "^10",
    "typescript": "^5"
  },
  "dependencies": {
    "@supabase/supabase-js": "^2"
  }
}
```

> If using pnpm: replace scripts with `pnpm` equivalents.

---

## 2) DB schema (Supabase)
Use this once (compatible with prior docs). Stores provenance + raw result JSON.

```sql
-- sites
create table if not exists sites (
  id uuid primary key default gen_random_uuid(),
  url text not null unique,
  slug text generated always as (regexp_replace(lower(url), '[^a-z0-9]+', '-', 'g')) stored,
  created_at timestamptz not null default now()
);
create index if not exists sites_slug_idx on sites(slug);

-- scans
create table if not exists scans (
  id uuid primary key default gen_random_uuid(),
  site_id uuid not null references sites(id) on delete cascade,
  status text not null default 'queued', -- queued|running|complete|error
  subscription_tier text default 'free',
  created_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  error text
);
create index if not exists scans_site_idx on scans(site_id);

-- scan_modules
create table if not exists scan_modules (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references scans(id) on delete cascade,
  module text not null,                  -- "sitecore","openapi","sitemap","json"
  data_source text not null,             -- "sitecore-graphql","openapi","sitemap","json-sample"
  confidence real not null default 0,
  requires_credentials boolean not null default false,
  duration_ms integer not null default 0,
  error text,
  created_at timestamptz not null default now()
);
create index if not exists scan_modules_scan_idx on scan_modules(scan_id);
create index if not exists scan_modules_module_idx on scan_modules(module);

-- analysis_results
create table if not exists analysis_results (
  id uuid primary key default gen_random_uuid(),
  scan_module_id uuid not null references scan_modules(id) on delete cascade,
  result jsonb not null,
  created_at timestamptz not null default now()
);
create index if not exists analysis_results_gin on analysis_results using gin(result jsonb_path_ops);
```

---

## 3) Shared packages

### `/packages/core/src/types.ts`
```ts
export type DataSource =
  | 'sitecore-graphql' | 'openapi' | 'sitemap' | 'json-sample';

export interface AnalyzerResult<T = unknown> {
  module: string;
  data: T | null;
  data_source: DataSource;
  confidence: number;        // 0..1
  requires_credentials?: boolean;
  error?: string;
  duration_ms: number;
  fetched_at?: string;
}
```

### `/packages/db/src/index.ts`
```ts
import { createClient } from '@supabase/supabase-js';

const url = process.env.SUPABASE_URL!;
const key = process.env.SUPABASE_SERVICE_ROLE!;
export const supabase = createClient(url, key, { auth: { persistSession: false } });

export async function ensureSite(urlStr: string) {
  const { data } = await supabase.from('sites').select('id').eq('url', urlStr).maybeSingle();
  if (data?.id) return data.id;
  const { data: inserted } = await supabase.from('sites').insert({ url: urlStr }).select('id').single();
  return inserted!.id;
}

export async function createScan(siteId: string) {
  const { data } = await supabase.from('scans').insert({ site_id: siteId, status: 'running', started_at: new Date().toISOString() }).select('id').single();
  return data!.id;
}

export async function finishScan(scanId: string, error?: string) {
  await supabase.from('scans').update({ status: error ? 'error' : 'complete', finished_at: new Date().toISOString(), error }).eq('id', scanId);
}

export async function saveModule(scanId: string, module: string, data_source: string, confidence: number, duration_ms: number, result: unknown, requires_credentials = false, error?: string) {
  const { data: mod } = await supabase.from('scan_modules').insert({ scan_id: scanId, module, data_source, confidence, duration_ms, requires_credentials, error }).select('id').single();
  await supabase.from('analysis_results').insert({ scan_module_id: mod!.id, result });
}
```

---

## 4) Sitecore GraphQL – schema & codegen

### Install extractor package structure
```
/packages/extractors/sitecore
  /queries
    contentTree.graphql
  codegen.yml
  enumerate.ts
  schema.graphql          # generated
  sitecore-sdk.ts         # generated
```

### `packages/extractors/sitecore/codegen.yml`
```yaml
schema: ./schema.graphql
documents:
  - ./queries/**/*.graphql
generates:
  ./sitecore-sdk.ts:
    plugins:
      - typescript
      - typescript-operations
      - typescript-graphql-request
    config:
      avoidOptionals: true
      enumsAsTypes: true
```

### `packages/extractors/sitecore/queries/contentTree.graphql`
```graphql
query ContentTree($path: String!, $first: Int!, $after: String) {
  item(path: $path) {
    id
    name
    template { name }
    children(first: $first, after: $after) {
      pageInfo { hasNextPage endCursor }
      results { id name path language template { name } }
    }
  }
}
```

### Enumerate & persist – `packages/extractors/sitecore/enumerate.ts`
```ts
import 'dotenv/config';
import { GraphQLClient } from 'graphql-request';
import { getSdk } from './sitecore-sdk';
import { ensureSite, createScan, finishScan, saveModule } from '@packages/db';

async function run(url: string) {
  const siteId = await ensureSite(url);
  const scanId = await createScan(siteId);
  const started = Date.now();

  try {
    const client = new GraphQLClient(process.env.SC_ENDPOINT!, {
      headers: { 'sc_apikey': process.env.SC_API_KEY! }
    });
    const sdk = getSdk(client);

    const path = '/sitecore/content';
    let after: string | null = null;
    const collected: any[] = [];

    do {
      const res = await sdk.ContentTree({ path, first: 50, after });
      const next = res.item?.children?.pageInfo?.hasNextPage;
      after = next ? res.item!.children!.pageInfo!.endCursor! : null;
      collected.push(...(res.item?.children?.results ?? []));
    } while (after);

    await saveModule(
      scanId,
      'sitecore',
      'sitecore-graphql',
      0.95,
      Date.now() - started,
      { path, count: collected.length, sample: collected.slice(0, 10) }
    );

    await finishScan(scanId);
    console.log(`OK – ${collected.length} items`);
  } catch (e: any) {
    await saveModule(scanId, 'sitecore', 'sitecore-graphql', 0, Date.now() - started, null, false, String(e.message || e));
    await finishScan(scanId, String(e.message || e));
    console.error('ERROR', e);
    process.exitCode = 1;
  }
}

// usage: pnpm enumerate:sitecore --url=https://example.com
const argUrl = process.argv.find(a => a.startsWith('--url='))?.split('=')[1] ?? 'https://example.com';
run(argUrl);
```

**Run**
```bash
pnpm gql:schema
pnpm gql:codegen
pnpm enumerate:sitecore --url=https://example.com
```

---

## 5) OpenAPI – generate types + enumerate

### Minimal layout
```
/packages/extractors/openapi
  types.d.ts          # generated
  enumerate.ts
```

### Generate types
```bash
OPENAPI_URL=https://example.com/openapi.json pnpm enumerate:openapi
```

### `packages/extractors/openapi/enumerate.ts`
```ts
import 'dotenv/config';
import { ensureSite, createScan, finishScan, saveModule } from '@packages/db';
import type { paths } from './types';

// Example using fetch; for large APIs, use openapi-fetch or a generated client
async function run(url: string) {
  const siteId = await ensureSite(url);
  const scanId = await createScan(siteId);
  const started = Date.now();
  try {
    // Example: GET /v1/articles
    const res = await fetch(`${url}/v1/articles`);
    if (!res.ok) throw new Error(`openapi ${res.status}`);
    const json: any = await res.json();

    await saveModule(scanId, 'openapi', 'openapi', 0.9, Date.now() - started, { endpoint: '/v1/articles', count: json?.length ?? 0, sample: json?.slice?.(0, 5) ?? json });
    await finishScan(scanId);
  } catch (e: any) {
    await saveModule(scanId, 'openapi', 'openapi', 0, Date.now() - started, null, false, String(e.message || e));
    await finishScan(scanId, String(e.message || e));
  }
}

const argUrl = process.argv.find(a => a.startsWith('--url='))?.split('=')[1] ?? 'https://api.example.com';
run(argUrl);
```

---

## 6) Sitemaps – enumerate public URLs for HTML parsers

### Layout
```
/packages/extractors/sitemap
  enumerate.ts
```

### `packages/extractors/sitemap/enumerate.ts`
```ts
import 'dotenv/config';
import { ensureSite, createScan, finishScan, saveModule } from '@packages/db';
import * as zlib from 'zlib';

async function fetchText(url: string) {
  const res = await fetch(url, { headers: { 'User-Agent': 'SMARTBot/1.0' } });
  if (!res.ok) throw new Error(`sitemap ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  const ct = res.headers.get('content-type') || '';
  const isGzip = /application\/gzip|\.gz$/.test(ct) || url.endsWith('.gz');
  return isGzip ? zlib.gunzipSync(buf).toString('utf8') : buf.toString('utf8');
}

async function run(url: string) {
  const siteId = await ensureSite(url);
  const scanId = await createScan(siteId);
  const started = Date.now();
  try {
    const robots = await fetchText(`${url.replace(/\/$/, '')}/robots.txt`).catch(() => '');
    const sitemapUrl = robots.match(/sitemap:\s*(\S+)/i)?.[1] || `${url.replace(/\/$/, '')}/sitemap.xml`;
    const xml = await fetchText(sitemapUrl);

    const urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);

    await saveModule(scanId, 'sitemap', 'sitemap', 0.8, Date.now() - started, { sitemapUrl, count: urls.length, sample: urls.slice(0, 20) });
    await finishScan(scanId);
  } catch (e: any) {
    await saveModule(scanId, 'sitemap', 'sitemap', 0, Date.now() - started, null, false, String(e.message || e));
    await finishScan(scanId, String(e.message || e));
  }
}

const argUrl = process.argv.find(a => a.startsWith('--url='))?.split('=')[1] ?? 'https://www.example.com';
run(argUrl);
```

---

## 7) JSON sample → TypeScript types (quicktype)

### Layout
```
/packages/extractors/json
  /samples   # put a few .json responses here
  types.ts   # generated
```

### Generate types
```bash
pnpm types:quick
```

Use `packages/extractors/json/types.ts` in your parsers for strong typing.

---

## 8) Sitecore fallback: SSC/SPE/SCS
If GraphQL introspection is disabled or not allowed:

- **SSC REST**: endpoints under `/sitecore/api/ssc/` (e.g., `item/{id}`); enumerate with authenticated GETs and persist JSON.
- **SPE (PowerShell)**: export items/templates to JSON/CSV; build a small uploader endpoint that accepts the file and stores to `analysis_results` with `data_source='json-sample'`.
- **SCS/CLI**: `sitecore ser pull` to produce YAML; parse with a YAML loader and persist normalized rows.

> Always store the *raw* payload + a normalized projection, and tag `data_source` and `fetched_at`.

---

## 9) Provenance & guardrails
- Add `User-Agent: SMARTBot/1.0` and respect `robots.txt` for public enumerations.
- Rate-limit and backoff on 429/5xx; never hammer endpoints.
- Encrypt any stored API keys; avoid storing them if you can.
- Log request method, URL, status, duration; store in your app logs (not DB) for audit.

---

## 10) One-liner runbook
```bash
# Sitecore (best path, requires creds)
pnpm gql:schema && pnpm gql:codegen && pnpm enumerate:sitecore --url=https://www.yoursite.com

# OpenAPI (if present)
OPENAPI_URL=https://api.yoursite.com/openapi.json pnpm enumerate:openapi --url=https://api.yoursite.com

# Sitemap (public)
pnpm enumerate:sitemap --url=https://www.yoursite.com
```

---

## 11) What “done” looks like (acceptance)
- Supabase tables populated with: a `scans` row, 1+ `scan_modules` rows, and an `analysis_results` row per module containing **real payloads**.
- Each result JSON includes counts + small samples for easy report rendering.
- No simulated data anywhere; failures are explicit and stored as module `error` with `confidence=0`.

---

### Notes
- You can wire these enumerators into the earlier **orchestrator** and **reporting** layers directly.
- When you later add Playwright/axe/headers analyzers, keep using `saveModule()` to persist results with `data_source` provenance.

