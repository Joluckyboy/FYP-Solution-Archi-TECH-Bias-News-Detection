/**
 * propagandaHighlight.js
 *
 * Shared phrase-matching logic for PropagandaTab and HighlightedArticle.
 * Single source of truth — no duplicated _cleanPhrase / _findContext logic.
 *
 * Key design: long paragraphs are split into sub-clauses so that multiple
 * phrases within the same paragraph each get a distinct _sentenceKey, allowing
 * all of them to appear as separate instances in PropagandaTab.
 */

export function cleanPhrase(raw) {
  return raw
    .replace(/##(\w+)/g, "$1")           // remove BERT subword prefix e.g. ##dding → dding
    .replace(/(\w)\s'\s(\w)/g, "$1'$2")
    .replace(/\s'\s/g, "'")
    .replace(/\s-\s/g, "-")
    .replace(/\s\/\s/g, "/")
    .replace(/,\s+(the\s+)?(official|he|she|they|trump|officials?|sources?|spokesman?)\s+said.*$/i, "")
    .replace(/\s+(the|a|an|and|or|but|of|in|on|at|to|for|with|by|from|as|that|this|also)\s*$/i, "")
    .replace(/\s+([.,;:!?])/g, "$1")
    .replace(/^[\s""''"`.,;:!?(){}—–]+/, "")
    .replace(/[\s""''"`.,;:!?(){}—–]+$/, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/**
 * Split a long text block into the smallest useful sub-clauses.
 *
 * Splits on (in order of preference):
 * 1. End of sentence inside/after a quote: ." or !" or ?" followed by space
 * 2. Plain sentence end: ". " or "! " or "? " followed by capital
 * 3. Comma followed by capital (new clause)
 *
 * Returns the original string as a single-element array if no splits found
 * or if the string is short enough already.
 */
function splitIntoSubClauses(text) {
  if (text.length <= 200) return [text];

  // Strategy: walk through and collect split points
  const splitPoints = [];

  for (let i = 0; i < text.length - 1; i++) {
    const ch   = text[i];
    const next = text[i + 1];
    const after = text[i + 2] ?? "";

    // End of quoted speech: ." or !" or ?"  followed by space + capital
    if ((ch === '"' || ch === '\u201d' || ch === "'") &&
        (next === ' ' || (next === ',' && after === ' '))) {
      splitPoints.push(i + 1);
      continue;
    }

    // Plain sentence end: . or ! or ? followed by space + capital
    if ((ch === '.' || ch === '!' || ch === '?') && next === ' ' && /[A-Z"']/.test(after)) {
      splitPoints.push(i + 1);
      continue;
    }

    // Comma followed by space + capital (new clause indicator)
    if (ch === ',' && next === ' ' && /[A-Z"']/.test(after)) {
      splitPoints.push(i + 1);
    }
  }

  if (!splitPoints.length) return [text];

  // Build sub-clauses from split points
  const clauses = [];
  let start = 0;
  for (const pt of splitPoints) {
    const clause = text.slice(start, pt).trim();
    if (clause.length > 15) clauses.push(clause);
    start = pt;
  }
  const last = text.slice(start).trim();
  if (last.length > 15) clauses.push(last);

  return clauses.length > 1 ? clauses : [text];
}

/**
 * findPhraseInContent
 *
 * 1. Splits articleContent into sentences
 * 2. Finds the best matching sentence for rawPhrase
 * 3. If that sentence is long (>200 chars), narrows to the best sub-clause
 * 4. Within the sub-clause, finds the tightest token span (capped at 120 chars)
 *
 * The sub-clause becomes the _sentenceKey, ensuring phrases from the same
 * paragraph get distinct keys and all show as separate PropagandaTab instances.
 *
 * Returns:
 *   { found: true, before, match, after, _sentenceKey }   — on success
 *   { found: false, cleanPhrase }                          — on failure
 *   null                                                   — if inputs missing
 */
export function findPhraseInContent(rawPhrase, articleContent) {
  if (!articleContent || !rawPhrase) return null;

  const cleaned = cleanPhrase(rawPhrase);
  const tokens  = cleaned
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(t => t.length > 2);

  if (!tokens.length) return { found: false, cleanPhrase: cleaned };

  // Flatten paragraphs so sentence splitting works on both structured and flat text
  const flat = articleContent.replace(/\n\n+/g, " ");

  // First pass: split on clear sentence boundaries
  const sentences = flat
    .split(/(?<=[.!?""''])\s+(?=[A-Z"''])/g)
    .map(s => s.trim())
    .filter(s => s.length > 15);

  if (!sentences.length) return { found: false, cleanPhrase: cleaned };

  // ── Step 1: find best matching sentence ──────────────────────────────────
  let bestSentence = null, bestScore = 0;
  for (const sentence of sentences) {
    const norm  = sentence.toLowerCase().replace(/[^a-z0-9\s]/g, " ");
    const score = tokens.filter(t => norm.includes(t)).length;
    if (score > bestScore) { bestScore = score; bestSentence = sentence; }
  }

  const minScore = Math.max(1, Math.floor(tokens.length * 0.4));
  if (!bestSentence || bestScore < minScore) return { found: false, cleanPhrase: cleaned };

  // ── Step 1b: narrow to best sub-clause for long sentences ─────────────────
  // This is the key fix: phrases from the same long paragraph now each get
  // a distinct _sentenceKey (their own sub-clause).
  if (bestSentence.length > 200) {
    const subClauses = splitIntoSubClauses(bestSentence);
    if (subClauses.length > 1) {
      let bestClause = null, bestClauseScore = 0;
      for (const clause of subClauses) {
        const norm  = clause.toLowerCase().replace(/[^a-z0-9\s]/g, " ");
        const score = tokens.filter(t => norm.includes(t)).length;
        if (score > bestClauseScore) {
          bestClauseScore = score;
          bestClause      = clause;
        }
      }
      // Only use sub-clause if it still matches well enough
      if (bestClause && bestClauseScore >= minScore) {
        bestSentence = bestClause;
      }
    }
  }

  // ── Step 2: find tight token span within the (sub-)sentence ──────────────
  const sentLower = bestSentence.toLowerCase().replace(/[^a-z0-9\s]/g, " ");
  const positions = [];

  for (const tok of tokens) {
    let from = 0;
    while (true) {
      const idx = sentLower.indexOf(tok, from);
      if (idx === -1) break;
      positions.push({ start: idx, end: idx + tok.length, tok });
      from = idx + 1;
    }
  }

  if (!positions.length) return { found: false, cleanPhrase: cleaned };
  positions.sort((a, b) => a.start - b.start);

  // Sliding window — find window with most unique token hits
  const windowSize = Math.min(tokens.length, positions.length);
  let bestStart  = positions[0].start;
  let bestEnd    = positions[windowSize - 1].end;
  let bestUnique = new Set(positions.slice(0, windowSize).map(p => p.tok)).size;

  for (let i = 1; i <= positions.length - windowSize; i++) {
    const wp      = positions.slice(i, i + windowSize);
    const wUnique = new Set(wp.map(p => p.tok)).size;
    if (wUnique > bestUnique) {
      bestStart  = wp[0].start;
      bestEnd    = wp[windowSize - 1].end;
      bestUnique = wUnique;
    }
  }

  // Expand to word boundaries
  let s = bestStart, e = bestEnd;
  while (s > 0 && !/\s/.test(bestSentence[s - 1])) s--;
  while (e < bestSentence.length && !/\s/.test(bestSentence[e])) e++;

  // Cap at 120 chars so huge sentences don't get entirely highlighted
  if (e - s > 120) {
    e = s + 120;
    while (e < bestSentence.length && !/\s/.test(bestSentence[e])) e++;
  }

  const match = bestSentence.slice(s, e).trim();
  if (!match) return { found: false, cleanPhrase: cleaned };

  return {
    found:        true,
    before:       bestSentence.slice(0, s),
    match,
    after:        bestSentence.slice(e),
    _sentenceKey: bestSentence,   // unique per sub-clause
  };
}