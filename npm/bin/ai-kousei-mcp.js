#!/usr/bin/env node
/* ai-kousei MCP server — stdio, zero dependencies.
 *
 * Exposes the same rule packs the CLI and the browser demo use, so an agent can
 * check its own Japanese before it writes a commit, a report or a customer reply.
 *
 *   claude mcp add ai-kousei -- npx -y ai-kousei ai-kousei-mcp
 */
"use strict";

const fs = require("fs");
const path = require("path");
const engine = require("../lint.js");

const RULES_DIR = path.join(__dirname, "..", "rules");
const PROFILES = ["commit", "report", "agent", "customer"];
const PROTOCOL = "2025-06-18";

for (const f of fs.readdirSync(RULES_DIR)) {
  if (f.endsWith(".json")) engine.setPacks({ [f.replace(/\.json$/, "")]: JSON.parse(fs.readFileSync(path.join(RULES_DIR, f), "utf8")) });
}

const TOOLS = [
  {
    name: "lint_japanese",
    description: "Check Japanese text against Japanese public writing standards (公用文作成の考え方 / JTF日本語標準スタイルガイド). Every finding carries the document and article it comes from. No LLM, no network.",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", description: "The Japanese text to check." },
        profile: { type: "string", enum: PROFILES, description: "commit: 常体 required. report: 敬体 allowed. agent: no vague wording. customer: 敬体 required. Default commit." },
        lang: { type: "string", description: "Rule pack, default ja." },
      },
      required: ["text"],
    },
  },
  {
    name: "japanese_metrics",
    description: "Measure the signals that separate AI written Japanese from human written Japanese: 敬体率, 受動態率, 指示語率, 抽象接尾辞率, 平均文長.",
    inputSchema: { type: "object", properties: { text: { type: "string" } }, required: ["text"] },
  },
];

function runTool(name, args) {
  const text = String((args && args.text) || "");
  if (!text.trim()) throw new Error("text is empty");
  if (name === "lint_japanese") {
    const profile = (args.profile && PROFILES.indexOf(args.profile) >= 0) ? args.profile : "commit";
    const r = engine.lint(text, args.lang || "ja", profile);
    const lines = r.findings.map(f => `- [${f.severity}] ${f.title}` + (f.fix ? `\n  直し方: ${f.fix}` : "") + (f.source ? `\n  根拠: ${f.source}` : ""));
    return `プロファイル: ${r.profileLabel} / スコア: ${r.score} / 判定: ${r.passed ? "合格" : "差し戻し"}\n` +
           `指摘: ${r.findings.length}件（error ${r.errors} / warn ${r.warns}）\n` + (lines.join("\n") || "指摘なし");
  }
  if (name === "japanese_metrics") {
    const m = engine.metrics(text);
    return Object.keys(m).map(k => `${k}: ${typeof m[k] === "number" ? m[k].toFixed(3) : m[k]}`).join("\n");
  }
  throw new Error("unknown tool: " + name);
}

function handle(msg) {
  const { id, method, params } = msg;
  if (method === "initialize") {
    return { protocolVersion: PROTOCOL, capabilities: { tools: {} }, serverInfo: { name: "ai-kousei", version: require("../package.json").version } };
  }
  if (method === "tools/list") return { tools: TOOLS };
  if (method === "tools/call") {
    try {
      return { content: [{ type: "text", text: runTool(params.name, params.arguments || {}) }] };
    } catch (e) {
      return { content: [{ type: "text", text: String(e.message || e) }], isError: true };
    }
  }
  if (method === "ping") return {};
  if (id === undefined) return null; // notification
  throw Object.assign(new Error("method not found: " + method), { code: -32601 });
}

let buf = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", chunk => {
  buf += chunk;
  let nl;
  while ((nl = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, nl).trim();
    buf = buf.slice(nl + 1);
    if (!line) continue;
    let msg;
    try { msg = JSON.parse(line); } catch (e) { continue; }
    let result, error;
    try { result = handle(msg); } catch (e) { error = { code: e.code || -32603, message: String(e.message || e) }; }
    if (msg.id === undefined) continue;
    process.stdout.write(JSON.stringify(error ? { jsonrpc: "2.0", id: msg.id, error } : { jsonrpc: "2.0", id: msg.id, result }) + "\n");
  }
});
