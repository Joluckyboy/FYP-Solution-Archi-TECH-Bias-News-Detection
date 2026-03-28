/**
 * highlightUtils.js
 *
 * Single consolidated utility file for all article highlighting logic.
 * Used by: ResultsPage, TrustSnapshot, HighlightedArticle, ArticleModal
 *
 * Exports:
 *   norm(text)                          — normalise unicode/whitespace
 *   findSentenceInContent(needle, hay)  — exact-first sentence finder (sentiment)
 *   findBestMatch(needle, hay)          — fuzzy match for factcheck (paraphrased)
 *   buildSentimentMatches(content, res) — [{sentence, label, start, end}]
 *   buildFactcheckMatches(content, res) — [{fact, start, end}]
 *   splitToParagraphs(content)          — split article into display paragraphs
 *   buildHlMap(matches)                 — char-index → match Map
 *   hlMapToSegs(content, hlMap, fn)     — [{key, parts}] for rendering
 *   getHighlightStyle(technique)        — {bg, color, label, def}
 *   getLegendItems(techniques)          — deduplicated legend array
 *   formatArticleParagraphs(content)    — structured paragraph array
 */

// ─── Normaliser ───────────────────────────────────────────────────────────────
// Converts all fancy unicode punctuation to plain ASCII equivalents so that
// DB sentences (which may use different quote/dash chars) match article text.
export function norm(text) {
  return (text || "")
    .normalize("NFKC")
    // curly/fancy single quotes → '
    .replace(/[\u2018\u2019\u201A\u201B\u2039\u203A\u2032\u2035\u0060]/g, "'")
    // curly/fancy double quotes → "
    .replace(/[\u201C\u201D\u201E\u201F\u275D\u275E\u00AB\u00BB\u2033\u2036]/g, '"')
    // all dash/minus variants including em-dash \u2014 and en-dash \u2013 → -
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D]/g, "-")
    // non-breaking & exotic spaces → regular space
    .replace(/[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000\uFEFF]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

// ─── Map a normalised [start,end] back to original character positions ────────
function normRangeToOrig(original, nHaystack, nStart, nEnd) {
  if (nStart < 0 || nEnd > nHaystack.length) return null;
  const needle = nHaystack.slice(nStart, nEnd);
  const nLen   = needle.length;
  const ratio  = original.length / (nHaystack.length || 1);
  for (const pad of [40, 120, 300, 600]) {
    const wOs  = Math.max(0, Math.floor(nStart * ratio) - pad);
    const wOe  = Math.min(original.length, Math.ceil(nEnd * ratio) + pad);
    const win  = original.slice(wOs, wOe);
    const wn   = norm(win);
    const wi   = wn.indexOf(needle);
    if (wi !== -1) {
      const wr = win.length / (wn.length || 1);
      return { start: wOs + Math.floor(wi * wr), end: wOs + Math.min(win.length, Math.ceil((wi + nLen) * wr)) };
    }
  }
  return null;
}

// ─── Exact-first sentence finder (for SENTIMENT) ─────────────────────────────
// DB sentences are verbatim from the article — exact normalised match should
// succeed almost always. Falls back to anchor-word then keyword-density.
export function findSentenceInContent(needle, haystack) {
  if (!needle || !haystack) return null;
  const nN = norm(needle), nH = norm(haystack);
  if (nN.length < 6) return null;

  // 1. Exact normalised
  let idx = nH.indexOf(nN);
  if (idx !== -1) return normRangeToOrig(haystack, nH, idx, idx + nN.length);

  // 2. Strip outer punctuation/quotes
  const stripped = nN.replace(/^[\s"'\-–—.!?,;:()]+|[\s"'\-–—.!?,;:()]+$/g, "");
  if (stripped.length > 10 && stripped !== nN) {
    idx = nH.indexOf(stripped);
    if (idx !== -1) return normRangeToOrig(haystack, nH, idx, idx + stripped.length);
  }

  // 3. First-N-words anchor (handles duplicate/truncated DB sentences)
  const words = nN.split(/\s+/).filter(Boolean);
  for (let w = Math.min(words.length, 12); w >= 5; w--) {
    const anchor = words.slice(0, w).join(" ");
    idx = nH.indexOf(anchor);
    if (idx !== -1) {
      let end = idx + anchor.length;
      for (let j = w; j < words.length; j++) {
        const nxt = nH.indexOf(words[j], end);
        if (nxt !== -1 && nxt - end <= 20) end = nxt + words[j].length;
        else break;
      }
      return normRangeToOrig(haystack, nH, idx, end);
    }
  }

  // 4. Keyword-density sentence scoring
  const segs = [];
  const re = /[^.!?\n]+(?:[.!?]+(?:["'\u201d])?|\n|$)/g;
  let m;
  while ((m = re.exec(haystack)) !== null) {
    const t = m[0].trim();
    if (t.length > 15) segs.push({ start: m.index, end: m.index + m[0].length, n: norm(t) });
  }
  const kw = nN.split(/\W+/).filter(w => w.length >= 4);
  if (!kw.length) return null;
  let best = 0, bestSeg = null;
  for (const s of segs) { const sc = kw.filter(w => s.n.includes(w)).length / kw.length; if (sc > best) { best = sc; bestSeg = s; } }
  if (bestSeg && best >= 0.4) return { start: bestSeg.start, end: bestSeg.end };
  return null;
}

// ─── Fuzzy match for FACTCHECK (statements may be paraphrased) ───────────────
export function findBestMatch(needle, haystack) {
  if (!needle || !haystack) return null;
  const nN = norm(needle), nH = norm(haystack);
  if (nN.length < 8) return null;

  // 1. Exact normalised match
  let idx = nH.indexOf(nN);
  if (idx !== -1) return normRangeToOrig(haystack, nH, idx, idx + nN.length);

  // 2. Strip punctuation and retry
  const stripped = nN.replace(/^[\s"'\-–—.!?,;:()]+|[\s"'\-–—.!?,;:()]+$/g, "");
  if (stripped.length > 15 && stripped !== nN) {
    idx = nH.indexOf(stripped);
    if (idx !== -1) return normRangeToOrig(haystack, nH, idx, idx + stripped.length);
  }

  // 3. Anchor sliding window (verbatim prefix/suffix)
  const words = nN.split(/\s+/).filter(Boolean);
  if (words.length >= 4) {
    for (let w = Math.min(words.length, 10); w >= 4; w--) {
      for (const slice of [words.slice(0, w).join(" "), words.slice(-w).join(" ")]) {
        idx = nH.indexOf(slice);
        if (idx !== -1) {
          let end = idx + slice.length;
          for (let j = w; j < words.length; j++) {
            const nxt = nH.indexOf(words[j], end);
            if (nxt !== -1 && nxt - end <= 20) end = nxt + words[j].length;
            else break;
          }
          return normRangeToOrig(haystack, nH, idx, end);
        }
      }
    }
  }

  // 4. Sentence-level keyword scoring — finds the best sentence in the article
  //    that shares the most content words with the statement
  const stopWords = new Set(["the","a","an","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","will","would","could","should","may","might",
    "of","in","on","at","to","for","with","by","from","as","or","and","but","not",
    "that","this","it","its","they","their","there","what","which","who","how","than"]);

  const kwNeedle = words.filter(w => w.length >= 3 && !stopWords.has(w));
  if (!kwNeedle.length) return null;

  // Split haystack into sentences
  const sentenceRe = /[^.!?\n]+(?:[.!?]+["'\u201d]?|\n|$)/g;
  let bestScore = 0, bestMatch = null;
  let m;
  while ((m = sentenceRe.exec(nH)) !== null) {
    const sentWords = new Set(m[0].split(/\W+/).filter(w => w.length >= 3 && !stopWords.has(w)));
    const hits = kwNeedle.filter(w => sentWords.has(w)).length;
    const score = hits / kwNeedle.length;
    if (score > bestScore) {
      bestScore = score;
      bestMatch = { nStart: m.index, nEnd: m.index + m[0].length };
    }
  }

  // 5. Also try scoring against sliding windows of 2-3 sentences combined
  //    (handles statements that span a sentence boundary)
  const allSents = [];
  const sentRe2 = /[^.!?\n]+(?:[.!?]+["'\u201d]?|\n|$)/g;
  while ((m = sentRe2.exec(nH)) !== null) allSents.push({ text: m[0], start: m.index, end: m.index + m[0].length });

  for (let i = 0; i < allSents.length - 1; i++) {
    const combined = allSents[i].text + allSents[i+1].text;
    const sentWords = new Set(combined.split(/\W+/).filter(w => w.length >= 3 && !stopWords.has(w)));
    const hits = kwNeedle.filter(w => sentWords.has(w)).length;
    const score = hits / kwNeedle.length;
    if (score > bestScore) {
      bestScore = score;
      bestMatch = { nStart: allSents[i].start, nEnd: allSents[i+1].end };
    }
  }

  // Only accept matches with ≥50% keyword overlap to avoid false positives
  if (bestMatch && bestScore >= 0.5) {
    return normRangeToOrig(haystack, nH, bestMatch.nStart, bestMatch.nEnd);
  }

  return null;
}

// ─── Build sentiment matches from DB sentence_sentiments ─────────────────────
// Exact verbatim finder for sentiment — DB sentences are copied verbatim from the article.
// We never lowercase or fuzzy-match; we just do a plain indexOf so positions are pixel-perfect.
// ─── Verbatim sentence finder (exact first, then smart fallbacks) ─────────────
function removeInternalDuplication(text) {
  // Detects "... A B C D E ... A B C D E ..." (DB artifact) and returns from 2nd occurrence
  const words = text.split(/\s+/);
  if (words.length < 10) return text;
  for (let i = 0; i < Math.floor(words.length / 2); i++) {
    const phrase = words.slice(i, i + 5).join(' ').toLowerCase();
    for (let j = i + 1; j <= words.length - 5; j++) {
      if (words.slice(j, j + 5).join(' ').toLowerCase() === phrase) {
        // Found repeated 5-word sequence — return from the second occurrence
        return words.slice(j).join(' ');
      }
    }
  }
  return text;
}

function findByKeywords(needle, haystack) {
  const words = needle.split(/\s+/).filter(w => w.length >= 4);
  if (words.length < 3) return null;
  const haystackLower = haystack.toLowerCase();
  const checkWords = words.slice(0, Math.min(6, words.length));
  let pos = 0;
  while (pos < haystack.length) {
    const idx = haystackLower.indexOf(checkWords[0].toLowerCase(), pos);
    if (idx === -1) break;
    const win = haystackLower.slice(idx, Math.min(haystack.length, idx + needle.length + 100));
    const matched = checkWords.filter(w => win.includes(w.toLowerCase())).length;
    if (matched >= Math.ceil(checkWords.length * 0.6)) {
      return { start: idx, end: Math.min(haystack.length, idx + needle.length) };
    }
    pos = idx + 1;
  }
  return null;
}

function findVerbatimSentence(needle, haystack, searchFrom = 0) {
  if (!needle || !haystack) return null;
  const n = needle.trim();
  if (n.length < 4) return null;

  // 1. Exact match in original text
  let idx = haystack.indexOf(n, searchFrom);
  if (idx !== -1) return { start: idx, end: idx + n.length };

  if (searchFrom > 0) return null;

  // 2. Normalised match on both sides (handles em-dash, curly quotes, etc.)
  const nN = norm(n);
  const nH = norm(haystack);
  let nIdx = nH.indexOf(nN, searchFrom);
  if (nIdx !== -1) {
    // Map normalised position back to original
    const r = normRangeToOrig(haystack, nH, nIdx, nIdx + nN.length);
    if (r) return r;
  }

  // 3. Strip internal DB duplication then retry
  const deduped = removeInternalDuplication(n);
  if (deduped !== n && deduped.length > 15) {
    idx = haystack.indexOf(deduped);
    if (idx !== -1) return { start: idx, end: idx + deduped.length };
    // Also try normalised deduped
    const nD = norm(deduped);
    nIdx = nH.indexOf(nD);
    if (nIdx !== -1) {
      const r = normRangeToOrig(haystack, nH, nIdx, nIdx + nD.length);
      if (r) return r;
    }
  }

  // 4. Sliding anchor — try progressively shorter prefixes, normalised
  const words = nN.split(/\s+/).filter(Boolean);
  for (let w = Math.min(words.length, 10); w >= 4; w--) {
    const anchor = words.slice(0, w).join(" ");
    nIdx = nH.indexOf(anchor, searchFrom);
    if (nIdx !== -1) {
      // Extend rightward as far as the sentence words match
      let end = nIdx + anchor.length;
      for (let j = w; j < words.length; j++) {
        const wIdx = nH.indexOf(words[j], end);
        if (wIdx !== -1 && wIdx - end <= 8) end = wIdx + words[j].length;
        else break;
      }
      const r = normRangeToOrig(haystack, nH, nIdx, end);
      if (r) return r;
    }
  }

  // 5. Keyword density fallback (last resort)
  return findByKeywords(n, haystack);
}

// ─── Build sentiment matches — exact verbatim, handles overlapping DB sentences ──
export function buildSentimentMatches(content, sentimentResult) {
  const sentences = sentimentResult?.sentence_sentiments;
  if (!Array.isArray(sentences) || !sentences.length || !content) return [];

  const raw = [];
  const matchedRanges = []; // Tracks claimed ranges so overlapping sentences find a free slot

  for (const s of sentences) {
    if (!s.sentence || !s.label) continue;

    let searchFrom = 0;
    let found = null;

    while (searchFrom < content.length) {
      const r = findVerbatimSentence(s.sentence, content, searchFrom);
      if (!r) break;

      // If this range is already fully covered by a previous match, try next occurrence
      const alreadyTaken = matchedRanges.some(mr => mr.start <= r.start && mr.end >= r.end);
      if (!alreadyTaken) { found = r; break; }

      searchFrom = r.start + 1;
    }

    if (!found) continue;
    raw.push({ sentence: s.sentence, label: s.label.toLowerCase(), start: found.start, end: found.end });
    matchedRanges.push({ start: found.start, end: found.end });
  }

  raw.sort((a, b) => a.start - b.start);
  const deduped = []; let lastEnd = -1;
  for (const m of raw) { if (m.start >= lastEnd) { deduped.push(m); lastEnd = m.end; } }
  return deduped;
}

// ─── Split a long text chunk into display paragraphs (preserves exact chars) ──
function splitIntoDisplayParas(text, sentencesPerPara = 3) {
  if (text.length <= 500) return [text];

  // Collect positions right after ". X" where X is uppercase (sentence boundaries)
  const splitPoints = [];
  for (let i = 0; i < text.length - 2; i++) {
    if (/[.!?]/.test(text[i]) && text[i + 1] === ' ' && /[A-Z"'\u201C\u2018]/.test(text[i + 2])) {
      splitPoints.push(i + 2); // new paragraph starts here (after the space)
    }
  }
  if (splitPoints.length < sentencesPerPara) return [text];

  // Take every Nth split point as a paragraph boundary
  const paraStarts = [0];
  for (let i = sentencesPerPara - 1; i < splitPoints.length; i += sentencesPerPara) {
    if (splitPoints[i] < text.length - 50) paraStarts.push(splitPoints[i]);
  }

  const paras = [];
  for (let i = 0; i < paraStarts.length; i++) {
    const start = paraStarts[i];
    const end = i + 1 < paraStarts.length ? paraStarts[i + 1] : text.length;
    paras.push(text.slice(start, end));
  }

  // Safety: charPos tracking depends on exact sum — bail if anything is off
  if (paras.reduce((s, p) => s + p.length, 0) !== text.length) return [text];
  return paras;
}

// ─── Segment content by highlight map (with display paragraph splitting) ──────
export function hlMapToSegs(content, hlMap, toPayload) {
  // First split on real structural breaks (double newlines)
  const rawChunks = content.split(/(\n\n+)/);

  // Expand long prose chunks into display-sized paragraphs
  const chunks = [];
  for (const raw of rawChunks) {
    if (/^\n+$/.test(raw)) { chunks.push(raw); continue; }
    chunks.push(...splitIntoDisplayParas(raw));
  }

  const result = []; let charPos = 0, pi = 0;
  for (const chunk of chunks) {
    if (/^\n+$/.test(chunk)) { charPos += chunk.length; continue; }
    const parts = []; let curText = '', curKey = null, curEntry = null;
    for (let i = 0; i < chunk.length; i++) {
      const entry = hlMap.get(charPos + i);
      const key = entry ? toPayload(entry).hlKey : null;
      if (key !== curKey) {
        if (curText) parts.push({ text: curText, ...(curKey ? toPayload(curEntry) : {}) });
        curText = chunk[i]; curKey = key; curEntry = entry;
      } else curText += chunk[i];
    }
    if (curText) parts.push({ text: curText, ...(curKey ? toPayload(curEntry) : {}) });
    result.push({ key: pi++, parts });
    charPos += chunk.length;
  }
  return result;
}

// ─── Build factcheck matches from DB factcheck_result ────────────────────────
export function buildFactcheckMatches(content, factcheckResult) {
  if (!Array.isArray(factcheckResult) || !factcheckResult.length || !content) return [];
  const raw = [];
  for (const fact of factcheckResult) {
    if (!fact.statement) continue;
    const r = findBestMatch(fact.statement, content);
    if (!r) continue;
    raw.push({ fact, start: r.start, end: r.end });
  }
  raw.sort((a, b) => a.start - b.start);
  const deduped = []; let lastEnd = -1;
  for (const m of raw) { if (m.start >= lastEnd) { deduped.push(m); lastEnd = m.end; } }
  return deduped;
}

// ─── Paragraph splitter ───────────────────────────────────────────────────────
export function splitToParagraphs(content) {
  const paras = content.split(/\n\n+/).filter(p => p.trim());
  if (paras.length > 1) return paras;
  const sents = content.replace(/\n\n+/g, " ").split(/(?<=[.!?])\s+(?=[A-Z"'\u201C])/g).map(s => s.trim()).filter(Boolean);
  const chunks = [];
  for (let i = 0; i < sents.length; i += 3) chunks.push(sents.slice(i, i + 3).join(" "));
  return chunks.length ? chunks : [content];
}

// ─── Build char-index highlight map ──────────────────────────────────────────
export function buildHlMap(matches) {
  const map = new Map();
  for (const m of matches) for (let i = m.start; i < m.end; i++) if (!map.has(i)) map.set(i, m);
  return map;
}


// ─── Propaganda technique styles ─────────────────────────────────────────────
const TECHNIQUE_COLORS = {
  "Loaded_Language":                             { bg: "#fef08a", color: "#854d0e", label: "Loaded Language",              def: "Uses emotionally charged words to influence feelings" },
  "Name_Calling,Labeling":                       { bg: "#fca5a5", color: "#991b1b", label: "Name Calling",                 def: "Attaches a negative label to provoke emotional reaction" },
  "Flag-Waving":                                 { bg: "#bfdbfe", color: "#1e40af", label: "Flag Waving",                  def: "Appeals to national pride or group identity" },
  "Doubt":                                       { bg: "#f59e0b", color: "#451a03", label: "Doubt",                        def: "Questions credibility without providing evidence" },
  "Appeal_to_fear-prejudice":                    { bg: "#e9d5ff", color: "#6b21a8", label: "Appeal to Fear",               def: "Builds support by instilling fear or prejudice" },
  "Repetition":                                  { bg: "#99f6e4", color: "#0f766e", label: "Repetition",                   def: "Repeats a message to bypass critical thinking" },
  "Exaggeration,Minimisation":                   { bg: "#fed7aa", color: "#c2410c", label: "Exaggeration / Minimisation",  def: "Overstates or understates facts to distort reality" },
  "Bandwagon":                                   { bg: "#d9f99d", color: "#3f6212", label: "Bandwagon",                    def: "Implies everyone agrees to pressure conformity" },
  "Slogans":                                     { bg: "#fbcfe8", color: "#9d174d", label: "Slogans",                      def: "Uses catchy phrases that oversimplify complex issues" },
  "Causal_Oversimplification":                   { bg: "#fb923c", color: "#7c2d12", label: "Causal Oversimplification",    def: "Reduces a complex issue to a single cause" },
  "Reductio_ad_hitlerum":                        { bg: "#f43f5e", color: "#881337", label: "Reductio ad Hitlerum",         def: "Discredits an idea by associating it with an extreme figure" },
  "Obfuscation,Intentional_Vagueness,Confusion": { bg: "#a78bfa", color: "#3b0764", label: "Obfuscation / Vagueness",     def: "Uses unclear language to hide true intent" },
  "Appeal_to_Authority":                         { bg: "#67e8f9", color: "#164e63", label: "Appeal to Authority",         def: "Cites an authority to validate a claim without expertise" },
  "Black-and-White_Fallacy":                     { bg: "#bfdbfe", color: "#1e3a8a", label: "Black & White Fallacy",       def: "Presents only two extreme options when others exist" },
  "Thought-terminating_Cliches":                 { bg: "#4ade80", color: "#14532d", label: "Thought-terminating Clichés", def: "Uses familiar phrases to shut down debate" },
  "Red_Herring":                                 { bg: "#fca5a5", color: "#7f1d1d", label: "Red Herring",                 def: "Introduces irrelevant information to distract from the issue" },
  "Straw_Men":                                   { bg: "#e879f9", color: "#701a75", label: "Straw Men",                   def: "Misrepresents an opponent's argument to attack it" },
  "Whataboutism":                                { bg: "#818cf8", color: "#1e1b4b", label: "Whataboutism",                def: "Deflects criticism by pointing to a different issue" },
};

export function getHighlightStyle(technique) {
  return TECHNIQUE_COLORS[technique] ?? { bg: "#e5e7eb", color: "#374151", label: technique, def: "An influence technique was detected." };
}

export function getLegendItems(techniques) {
  return techniques
    .map(t => TECHNIQUE_COLORS[t] ?? null)
    .filter(Boolean)
    .filter((item, idx, self) => idx === self.findIndex(i => i.label === item.label));
}

// ─── Article paragraph formatter (from formatArticleParagraphs.js) ────────────
const TARGET_PARAGRAPH_LENGTH = 320;
const MIN_PARAGRAPH_LENGTH    = 180;

function normalizeText(content) {
  if (typeof content !== "string") return "";
  return content.replace(/\r\n?/g, "\n").trim();
}

function normalizeInlineSpacing(text) { return text.replace(/[ \t]+/g, " ").trim(); }

function splitByExistingStructure(text) {
  if (!text.includes("\n")) return [];
  const blocks = text.split(/\n{2,}/).map(p => p.trim()).filter(Boolean);
  if (blocks.length > 1) return blocks;
  const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
  if (lines.length > 1) return lines;
  return [];
}

function splitPlainTextBlob(text) {
  const normalized = normalizeInlineSpacing(text);
  const sentences  = normalized.match(/[^.!?]+(?:[.!?]+["')\]]*)?|[^.!?]+$/g)?.map(s => s.trim()).filter(Boolean) ?? [];
  if (sentences.length < 2) {
    const words = normalized.split(/\s+/).filter(Boolean);
    if (words.length <= 60) return [normalized];
    const chunks = [];
    for (let i = 0; i < words.length; i += 55) chunks.push(words.slice(i, i + 55).join(" "));
    return chunks;
  }
  const grouped = []; let cur = "";
  for (const s of sentences) {
    const candidate = cur ? `${cur} ${s}` : s;
    if (cur && candidate.length > TARGET_PARAGRAPH_LENGTH && cur.length >= MIN_PARAGRAPH_LENGTH) { grouped.push(cur); cur = s; continue; }
    cur = candidate;
  }
  if (cur) grouped.push(cur);
  if (grouped.length === 1 && sentences.length >= 4) {
    const chunks = [];
    for (let i = 0; i < sentences.length; i += 3) chunks.push(sentences.slice(i, i + 3).join(" "));
    return chunks.map(p => p.trim()).filter(Boolean);
  }
  return grouped.map(p => p.trim()).filter(Boolean);
}

export function formatArticleParagraphs(content) {
  const text = normalizeText(content);
  if (!text) return [];
  const structured = splitByExistingStructure(text);
  if (structured.length) return structured;
  return splitPlainTextBlob(text);
}