#!/usr/bin/env node
/* buntai — Japanese writing linter. Node build.
 *
 * Same rules, same engine as the Python package and the browser demo: the
 * rule packs in rules/ are the single source, lint.js is shared verbatim.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const engine = require("../lint.js");

const RULES_DIR = path.join(__dirname, "..", "rules");
const PROFILES = ["commit", "report", "agent", "customer"];

function loadPacks() {
  const packs = {};
  for (const f of fs.readdirSync(RULES_DIR)) {
    if (f.endsWith(".json")) packs[f.replace(/\.json$/, "")] = JSON.parse(fs.readFileSync(path.join(RULES_DIR, f), "utf8"));
  }
  engine.setPacks(packs);
  return packs;
}

function readInput(args) {
  const mi = args.indexOf("-m");
  if (mi >= 0 && args[mi + 1] !== undefined) return args[mi + 1];
  const file = args.find((a, i) => !a.startsWith("-") && i > 0 && args[i - 1] !== "-m" &&
                                   args[i - 1] !== "--profile" && args[i - 1] !== "--lang");
  if (file && fs.existsSync(file)) return fs.readFileSync(file, "utf8");
  return fs.readFileSync(0, "utf8");
}

function flag(args, name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
}

function cmdLint(args) {
  const packs = loadPacks();
  const text = readInput(args);
  const profile = flag(args, "--profile", "commit");
  if (PROFILES.indexOf(profile) < 0) {
    console.error("unknown profile: " + profile + " (" + PROFILES.join(" | ") + ")");
    return 2;
  }
  const r = engine.lint(text, flag(args, "--lang", null), profile);
  if (args.includes("--json")) {
    console.log(JSON.stringify(r, null, 2));
    return r.passed ? 0 : 1;
  }
  if (!r.lang) {
    console.log("buntai: language not detected. Japanese is the sourced pack; force with --lang ja");
    return 0;
  }
  const fs_ = r.findings;
  if (fs_.length) console.log("next: " + (fs_[0].fix || fs_[0].title));
  console.log(packs[r.lang].name + " / " + r.profileLabel + "  score " + r.score + "/100  errors " +
              r.errors + "  warnings " + r.warns + "  " + (r.passed ? "[passes]" : "[blocked]"));
  const cap = args.includes("--all") ? fs_.length : 5;
  fs_.slice(0, cap).forEach((f, i) => {
    console.log((i + 1) + ". [" + (f.severity === "error" ? "ERROR" : "warn ") + "] " + f.title +
                (f.fix ? "  -> " + f.fix : ""));
    if (f.match) console.log("     found: " + f.match);
    if (f.source) console.log("     src:   " + f.source);
    console.log("     rule:  " + f.id);
  });
  if (fs_.length > cap) console.log((fs_.length - cap) + " more, run with --all");
  if (!fs_.length) console.log("  no findings");
  return r.passed ? 0 : 1;
}

function cmdRules(args) {
  const packs = loadPacks();
  const lang = flag(args, "--lang", "ja");
  const p = packs[lang];
  if (!p) { console.error("unknown lang: " + lang); return 2; }
  const srcs = p.sources || {};
  Object.keys(srcs).forEach(k => console.log("  " + k + "  " + (srcs[k].title || "") + "  " + (srcs[k].url || "")));
  console.log("");
  (p.rules || []).forEach(r => {
    const s = r.source || {}, doc = srcs[s.doc] || {}, ex = r.example || {};
    console.log(r.id + "  [" + r.severity + "]\n  " + r.title);
    if (s.loc) console.log("  src:    " + (doc.title || s.doc) + " " + s.loc);
    if (s.quote) console.log("  quote:  " + s.quote);
    if (ex.before) console.log("  AS-IS   " + ex.before.split("\n").join("\n          "));
    if (ex.after) console.log("  TO-BE   " + ex.after.split("\n").join("\n          "));
    console.log("");
  });
  return 0;
}

function cmdTemplate(args) {
  const packs = loadPacks();
  const p = packs[flag(args, "--lang", "ja")];
  if (!p) return 2;
  const kind = args.includes("--pr") ? "pr" : args.includes("--report") ? "report" : "commit";
  console.log((p.template || {})[kind] || "");
  return 0;
}

function cmdHook() {
  const gitDir = path.join(process.cwd(), ".git");
  if (!fs.existsSync(gitDir)) { console.error("not a git repository"); return 2; }
  const hooks = path.join(gitDir, "hooks");
  fs.mkdirSync(hooks, { recursive: true });
  const p = path.join(hooks, "commit-msg");
  fs.writeFileSync(p, "#!/bin/sh\n# buntai commit-msg hook\ncase \"$2\" in merge|squash|fixup) exit 0;; esac\nnpx --no-install buntai lint \"$1\" || exit 1\n", { mode: 0o755 });
  console.log("installed " + p);
  return 0;
}

function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];
  if (!cmd || cmd === "-h" || cmd === "--help") {
    console.log([
      "buntai — 日本語の文体リンター / Japanese writing linter",
      "",
      "  buntai lint <file>|-m \"text\" [--profile commit|report|agent|customer] [--lang ja] [--json] [--all]",
      "  buntai rules [--lang ja]      規則と出典と AS-IS/TO-BE",
      "  buntai template [--pr|--report]",
      "  buntai hook                   commit-msg フックを入れる",
      "",
      "error があると exit 1。warning は表示のみ。"
    ].join("\n"));
    return 0;
  }
  if (cmd === "lint") return cmdLint(args);
  if (cmd === "rules") return cmdRules(args);
  if (cmd === "template") return cmdTemplate(args);
  if (cmd === "hook") return cmdHook();
  console.error("unknown command: " + cmd);
  return 2;
}

process.exit(main());
