// Builds Monster Roommates for RUN: dist/index.html plus RUN's SDK bundled as one classic script
// (dist/rundot-sdk.js), loaded before the game so that window.RundotGameAPI exists when the game starts.
// By MV2 of Munim, Inc., made with AI agents. Apache-2.0. RUN's SDK keeps its own licence.
//
//   npm install && node build_run.mjs <out-folder>     ->  <out>/dist (deploy this), <out>/build-report.json
import { build } from "esbuild";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const out = path.resolve(process.argv[2] || "run-dist");
const dist = path.join(out, "dist");
const sdkDir = path.join("node_modules", "@series-inc", "rundot-game-sdk");
fs.mkdirSync(dist, { recursive: true });

// the SDK's browser API; Node-only modules it may mention are left out (they would only fail if called)
const NODE_ONLY = ["fs", "path", "os", "crypto", "child_process", "net", "tls", "http", "https", "zlib",
  "stream", "url", "util", "events", "buffer", "worker_threads", "module", "dns", "readline"];
const result = await build({
  stdin: {
    contents: "import RundotGameAPI from '@series-inc/rundot-game-sdk/api';\nwindow.RundotGameAPI = RundotGameAPI;\n",
    resolveDir: process.cwd(), loader: "js", sourcefile: "run-sdk-entry.js",
  },
  bundle: true, format: "iife", platform: "browser", target: "es2020", minify: true,
  outfile: path.join(dist, "rundot-sdk.js"),
  external: NODE_ONLY.flatMap((m) => [m, "node:" + m]),
  define: { "process.env.NODE_ENV": '"production"' },
  metafile: true, logLevel: "info",
});

const tag = '<script id="logic">';
let html = fs.readFileSync("index.html", "utf8");
if (!html.includes(tag)) throw new Error("index.html has no logic script");
html = html.replace(tag, '<script src="rundot-sdk.js"></script>\n' + tag);
fs.writeFileSync(path.join(dist, "index.html"), html);

const pkg = JSON.parse(fs.readFileSync(path.join(sdkDir, "package.json"), "utf8"));
const report = {
  sdk_version: pkg.version,
  sdk_license: pkg.license,
  sdk_bytes: fs.statSync(path.join(dist, "rundot-sdk.js")).size,
  index_bytes: Buffer.byteLength(html),
  bundled_inputs: Object.keys(result.metafile.inputs).length,
  warnings: result.warnings.length,
  game_version: (html.match(/Monster Roommates v(\d+\.\d+\.\d+)/) || [])[1] || "",
};

// the SDK's licence, kept beside the build (not inside dist) so it can be read before deploying
for (const name of ["LICENSE.md", "LICENSE", "LICENSE.txt"]) {
  const p = path.join(sdkDir, name);
  if (fs.existsSync(p)) { fs.copyFileSync(p, path.join(out, "RUNDOT-SDK-" + name)); report.sdk_license_file = name; }
}

// every SDK method the game calls should appear in the SDK's own type definitions
const CALLS = ["getItem", "setItem", "resolveLaunchIntent", "shareLinkAsync", "isRewardedAdReadyAsync",
  "showRewardedAdAsync", "submitMessageAsync", "submitScore", "appStorage", "notifications", "leaderboard"];
const dts = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p); else if (p.endsWith(".d.ts")) dts.push(p);
  }
})(path.join(sdkDir, "dist"));
const types = dts.map((p) => fs.readFileSync(p, "utf8")).join("\n");
report.calls_in_types = Object.fromEntries(CALLS.map((c) => [c, new RegExp("\\b" + c + "\\b").test(types)]));

// a smoke check: run the bundle in a bare window-like sandbox and list what RundotGameAPI offers
const sandbox = { console: { log() {}, warn() {}, error() {}, info() {}, debug() {} }, setTimeout, clearTimeout,
  setInterval, clearInterval, queueMicrotask, Promise, URL, URLSearchParams, TextEncoder, TextDecoder,
  navigator: { userAgent: "node", language: "en" }, location: { href: "https://example.invalid/", search: "", hash: "", origin: "https://example.invalid" },
  addEventListener() {}, removeEventListener() {}, postMessage() {}, document: { addEventListener() {}, createElement: () => ({ style: {} }), head: { appendChild() {} }, body: { appendChild() {} } } };
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.globalThis = sandbox; sandbox.parent = sandbox; sandbox.top = sandbox;
try {
  vm.runInNewContext(fs.readFileSync(path.join(dist, "rundot-sdk.js"), "utf8"), sandbox, { timeout: 5000 });
  const api = sandbox.RundotGameAPI;
  report.smoke = api ? { ok: true, keys: Object.keys(api).sort().slice(0, 80),
    has: Object.fromEntries(["appStorage", "app", "social", "ads", "notifications", "leaderboard"].map((k) => [k, !!api[k]])) } : { ok: false, error: "RundotGameAPI not set" };
} catch (e) {
  report.smoke = { ok: false, error: String((e && e.message) || e).slice(0, 400) };
}

fs.writeFileSync(path.join(out, "build-report.json"), JSON.stringify(report, null, 1));
console.log(JSON.stringify(report, null, 1));
