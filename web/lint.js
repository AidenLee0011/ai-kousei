// buntai engine. Shared by the browser demo and the npm CLI so that a
// finding on the page and a finding in CI can never disagree.
// Rules live in rules/*.json and are loaded by the caller.

(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.buntai = factory();
}(typeof self !== 'undefined' ? self : this, function () {
const LANGS = ["_common","ja","ko","zh","de","fr","es"];
const PACKS = {};
const CORPUS = {
  polite_rate:  {human:0.010, llm:0.717, label:"敬体率"},
  passive_rate: {human:0.000, llm:0.148, label:"受身率"},
  demonstrative_rate:{human:0.021, llm:0.324, label:"指示語率"},
  suffix_abstract_rate:{human:0.010, llm:0.191, label:"抽象名詞化率"},
  mean_len:     {human:24.7,  llm:39.7,  label:"一文平均字数"}
};
const EN_LABELS = {
  subject_long:{title:"subject {w} > {max} columns",why:"",fix:"Move the detail into the body."},
  subject_period:{title:"subject ends with a period",why:"",fix:"Drop the trailing period."},
  bullets:{title:"{n} bullets in the body",why:"",fix:"Keep the {max} that matter."},
  sections:{title:"report sections missing: {missing}",why:"",fix:"Use buntai template --lang {lang}."},
  sentence_long:{title:"sentence of {n} characters > {max}",why:"",fix:"Split the sentence."},
  max_ten:{title:"{n} commas in one sentence > {max}",why:"",fix:"Split the sentence or use a list."},
  kanji_run:{title:"{n} ideographs in a row > {max}",why:"",fix:"Break the compound."},
  heading_order:{title:"mixed enumeration markers",why:"",fix:"Use one order."}
};
const SAMPLES = {
  ja:{ai:"feat: 商品詳細APIにRedisキャッシュを追加\n\n商品詳細APIの応答速度向上とデータベース負荷軽減のため、Redisキャッシュを導入しました。\nキャッシュの有効期限（TTL）は300秒に設定されています。\n- **重要**: 監視対象に追加しました",
      human:"fix: 商品詳細APIにRedisキャッシュを追加\n\nなぜ: 商品詳細APIの応答が遅く、DB負荷も高い\nなにを: Redis を前段に追加。TTL 300秒\n確認: p95 820ms → 210ms"},
  jaReport:{
    ai:`件名: キャッシュ改善の件

本日、キャッシュ機構の全面刷新を行いました。これにより、応答速度が大幅に改善されたと考えております。`,
    human:`件名: 商品詳細APIの応答改善について（報告）

1 概要  Redis 追加により p95 応答を短縮
2 対応  Redis を前段に追加。TTL 300秒
3 結果  p95 820ms → 210ms
以上`},
  ko:{ai:"feat: 개선\n\n다음과 같습니다. 성능이 매우 개선된 것 같습니다.\n함께 살펴보겠습니다.",
      human:"fix: 결제 재시도 상한 3회로 변경\n\n왜: 재시도가 무한 반복되어 큐가 밀림\n무엇: retry_max 를 3 으로 고정\n확인: 부하 테스트 1시간, 큐 적체 0"},
  zh:{ai:"feat: 优化\n\n首先，本次改动显著提升了性能。其次，代码可读性也得到了改善。\n希望本次变更对您有所帮助。",
      human:"fix: 支付重试上限改为 3 次\n\n为什么: 重试无限循环，队列积压\n改动: retry_max 固定为 3\n验证: 压测 1 小时，队列积压 0"},
  de:{ai:"feat: Diverse Anpassungen\n\nIn der heutigen digitalen Welt ist es wichtig zu beachten, dass die Performance erheblich verbessert wurde.",
      human:"fix: Zahlungswiederholungen auf drei begrenzt\n\nWarum: Wiederholungen liefen endlos\nWas: retry_max auf 3 gesetzt\nGeprüft: Lasttest eine Stunde, kein Rückstau"},
  fr:{ai:"feat: Corrections diverses\n\nDans le monde d'aujourd'hui, il est important de noter que les performances ont été considérablement améliorées.",
      human:"fix: limite des tentatives de paiement fixée à trois\n\nPourquoi: les tentatives bouclaient sans fin\nQuoi: retry_max à 3\nVérifié: test de charge d'une heure, file à zéro"},
  es:{ai:"feat: Varias correcciones\n\nEn el mundo actual, es importante destacar que el rendimiento mejoró considerablemente.",
      human:"fix: limite de reintentos de pago fijado en tres\n\nPor qué: los reintentos se repetian sin fin\nQué: retry_max fijado en 3\nVerificado: prueba de carga de una hora, cola en cero"}
};

const esc = s => String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
const rx = (p,f) => new RegExp(p, f || "");
function width(s){ let n=0; for (const c of s) n += /[ᄀ-ᅟ⺀-꓏가-힣豈-﫿︰-﹏＀-｠￠-￦]/.test(c) ? 2 : 1; return n; }

function splitMessage(text){
  const lines = text.replace(/\r\n/g,"\n").split("\n").filter(l => !l.startsWith("#"));
  while (lines.length && !lines[0].trim()) lines.shift();
  if (!lines.length) return ["",""];
  return [lines[0].trim(), lines.slice(1).join("\n").replace(/^\n+|\n+$/g,"")];
}
function detectLang(text){
  const sc = {};
  for (const lang of LANGS){
    if (lang === "_common" || !PACKS[lang]) continue;
    const det = PACKS[lang].detect || {}; let s = 0;
    if (det.script) s += (text.match(rx(det.script,"g")) || []).length * (det.weight || 1);
    for (const w of (det.stopwords || [])) s += (text.match(rx("(?:^|[^\\w])" + w + "(?![\\w])","gi")) || []).length * (det.weight || 1);
    if (s) sc[lang] = s;
  }
  let best = null;
  for (const k in sc) if (best === null || sc[k] > sc[best]) best = k;
  if (best && sc.ja && /[぀-ゟ゠-ヿ]/.test(text)) best = "ja";
  return best && sc[best] >= 2 ? best : null;
}
function label(st, key, kw){
  const base = Object.assign({}, EN_LABELS[key], (st.labels || {})[key] || {});
  const out = {};
  for (const k in base) out[k] = String(base[k]).replace(/\{(\w+)\}/g, (m,p) => kw[p] !== undefined ? kw[p] : m);
  return out;
}
function structural(pack, subject, body){
  const out = [], st = pack.structural || {}, lang = pack.lang;
  if (st.subject_max_width && subject && width(subject) > st.subject_max_width)
    out.push(Object.assign({id:lang+"-subject-too-long",severity:"warn",weight:6,match:subject.slice(0,40)}, label(st,"subject_long",{w:width(subject),max:st.subject_max_width})));
  if (st.subject_no_period && subject && rx(st.subject_no_period).test(subject))
    out.push(Object.assign({id:lang+"-subject-period",severity:"warn",weight:3,match:""}, label(st,"subject_period",{})));
  if (st.bullet_max){
    const n = (body.match(/^\s*(?:[-*]|\d+[.)])\s+/gm) || []).length;
    if (n > st.bullet_max) out.push(Object.assign({id:lang+"-bullet-flood",severity:"warn",weight:7,match:""}, label(st,"bullets",{n:n,max:st.bullet_max})));
  }
  if ((st.body_sections||[]).length && body.split("\n").filter(l=>l.trim()).length >= 2){
    const miss = st.body_sections.filter(s => body.toLowerCase().indexOf(s.toLowerCase()) < 0);
    if (miss.length) out.push(Object.assign({id:lang+"-missing-sections",severity:"warn",weight:5,match:""}, label(st,"sections",{missing:miss.join("、"),lang:lang})));
  }
  const sents = body.split(/[。\n]/).filter(s => s.trim());
  if (st.sentence_max_chars){
    const long = sents.find(s => s.length > st.sentence_max_chars);
    if (long) out.push(Object.assign({id:lang+"-sentence-too-long",severity:"warn",weight:7,match:long.slice(0,40)}, label(st,"sentence_long",{n:long.length,max:st.sentence_max_chars})));
  }
  if (st.max_ten){
    const many = sents.find(s => (s.match(/、/g)||[]).length > st.max_ten);
    if (many) out.push(Object.assign({id:lang+"-max-ten",severity:"warn",weight:6,match:many.slice(0,40)}, label(st,"max_ten",{n:(many.match(/、/g)||[]).length,max:st.max_ten})));
  }
  if (st.kanji_run_max){
    const m = body.match(new RegExp("[\\u4E00-\\u9FFF]{" + (st.kanji_run_max+1) + ",}"));
    if (m) out.push(Object.assign({id:lang+"-kanji-run",severity:"warn",weight:5,match:m[0]}, label(st,"kanji_run",{n:m[0].length,max:st.kanji_run_max})));
  }
  if (st.heading_order){
    const kinds = new Set();
    body.split("\n").forEach(l => {
      const s = l.trim();
      if (/^[-*]\s/.test(s)) kinds.add("dash");
      else if (/^[・]\s?/.test(s)) kinds.add("nakaten");
      else if (/^\d+[.)．）]\s?/.test(s)) kinds.add("digit");
      else if (/^[①-⑳]/.test(s)) kinds.add("circled");
      else if (/^[ア-ン][.、)）]\s?/.test(s)) kinds.add("kana");
    });
    if (kinds.size > 1) out.push(Object.assign({id:lang+"-heading-order",severity:"warn",weight:6,match:[...kinds].join("/")}, label(st,"heading_order",{})));
  }
  const tone = st.tone;
  if (tone && body && rx(tone.a,"g").test(body+"\n") && rx(tone.b,"g").test(body+"\n"))
    out.push({id:lang+"-tone-mix",severity:"warn",weight:8,title:tone.title,why:tone.why,fix:tone.fix,source:tone.source||"",match:""});
  return out;
}
function cite(pack, src){
  if (!src) return "";
  const doc = (pack.sources || {})[src.doc] || {};
  return ((doc.title || src.doc || "") + " " + (src.loc || "")).trim();
}
function lint(text, forced, profile){
  const [subject, body] = splitMessage(text);
  const full = (subject + "\n" + body).trim();
  const lang = forced || detectLang(full);
  const findings = [];
  const prof = ((PACKS[lang]||{}).profiles||{})[profile||'commit'] || {};
  const off = new Set(prof.off || []);
  const active = [PACKS._common].concat(lang && PACKS[lang] ? [PACKS[lang]] : []);
  for (const pack of active){
    for (const r of (pack.rules || [])){
      if ((r.profiles && r.profiles.indexOf(profile||'commit') < 0) || off.has(r.id)) continue;
      const scope = r.scope || "any";
      const target = scope === "subject" ? subject : scope === "body" ? body : full;
      if (!target) continue;
      const m = rx(r.pattern, r.flags || "").exec(target);
      if (!m) continue;
      const loc = (r.i18n || {})[lang] || {};
      findings.push({id:r.id, severity:r.severity||"warn", weight:r.weight||5,
        title:loc.title||r.title, why:loc.why||r.why, fix:loc.fix||r.fix,
        source:cite(pack, r.source), example:r.example, match:m[0].slice(0,60)});
    }
  }
  if (lang && PACKS[lang]) findings.push.apply(findings, structural(PACKS[lang], subject, body).filter(f => !off.has(f.id)));
  findings.sort((a,b) => (a.severity===b.severity ? b.weight-a.weight : a.severity==="error" ? -1 : 1));
  const errors = findings.filter(f => f.severity === "error").length;
  return {lang, profile: profile||'commit', profileLabel: prof.label || (profile||'commit'), findings, errors, warns: findings.length-errors,
          score: Math.max(0, 100 - findings.reduce((s,f)=>s+f.weight,0)), passed: errors === 0};
}

// Deterministic signals, same definitions as buntai/metrics.py
function metrics(text){
  const body = text.split("\n").slice(1).join("\n").trim() || text;
  const s = body.split(/[。．\n]+/).map(x=>x.trim()).filter(Boolean);
  const n = s.length || 1;
  const rate = re => s.filter(x => re.test(x)).length / n;
  return {
    polite_rate: rate(/(?:です|ます|ました|ません)$/),
    passive_rate: rate(/され(?:る|た|て|ます|ました|ている)/),
    demonstrative_rate: s.reduce((a,x)=>a+(x.match(/これ|それ|この|その|そのため|これにより/g)||[]).length,0)/n,
    suffix_abstract_rate: s.reduce((a,x)=>a+(x.match(/[一-鿿]的|[一-鿿]性|[一-鿿]化/g)||[]).length,0)/n,
    mean_len: s.reduce((a,x)=>a+x.length,0)/n
  };
}


  return { setPacks: function (p) { Object.keys(p).forEach(function (k) { PACKS[k] = p[k]; }); },
           PACKS: PACKS, LANGS: LANGS, SAMPLES: SAMPLES, CORPUS: CORPUS,
           lint: lint, metrics: metrics, detectLang: detectLang, splitMessage: splitMessage };
}));
