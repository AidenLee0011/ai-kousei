#!/usr/bin/env node
/* Smoke test for the MCP server: handshake, tool list, one lint, one metrics run. */
"use strict";
const assert = require("assert");
const { spawn } = require("child_process");
const path = require("path");

const msgs = [
  { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "1" } } },
  { jsonrpc: "2.0", method: "notifications/initialized" },
  { jsonrpc: "2.0", id: 2, method: "tools/list" },
  { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "lint_japanese", arguments: { text: "feat: キャッシュ追加\n\nRedisキャッシュを導入しました。", profile: "commit" } } },
  { jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "japanese_metrics", arguments: { text: "導入しました。改善されました。" } } },
  { jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "lint_japanese", arguments: { text: "" } } },
];

const p = spawn(process.execPath, [path.join(__dirname, "bin", "ai-kousei-mcp.js")]);
let out = "";
p.stdout.on("data", d => { out += d; });
p.on("close", () => {
  const got = {};
  for (const line of out.split("\n").filter(Boolean)) { const m = JSON.parse(line); got[m.id] = m; }
  assert.strictEqual(got[1].result.serverInfo.name, "ai-kousei");
  assert.deepStrictEqual(got[2].result.tools.map(t => t.name), ["lint_japanese", "japanese_metrics"]);
  assert.ok(/敬体/.test(got[3].result.content[0].text), "polite body finding missing");
  assert.ok(/根拠/.test(got[3].result.content[0].text), "citation missing");
  assert.ok(/polite_rate: 1\.000/.test(got[4].result.content[0].text), "metrics wrong");
  assert.strictEqual(got[5].result.isError, true, "empty text should be an error");
  console.log("mcp smoke test PASS");
});
msgs.forEach(m => p.stdin.write(JSON.stringify(m) + "\n"));
setTimeout(() => p.stdin.end(), 500);
