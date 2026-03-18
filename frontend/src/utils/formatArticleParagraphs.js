const TARGET_PARAGRAPH_LENGTH = 320;
const MIN_PARAGRAPH_LENGTH = 180;

const normalizeText = (content) => {
  if (typeof content !== "string") return "";
  return content.replace(/\r\n?/g, "\n").trim();
};

const normalizeInlineSpacing = (text) => text.replace(/[ \t]+/g, " ").trim();

const splitByExistingStructure = (text) => {
  if (!text.includes("\n")) return [];

  const blocksByBlankLines = text
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  if (blocksByBlankLines.length > 1) return blocksByBlankLines;

  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length > 1) return lines;

  return [];
};

const splitPlainTextBlob = (text) => {
  const normalized = normalizeInlineSpacing(text);
  const sentences = normalized.match(/[^.!?]+(?:[.!?]+["')\]]*)?|[^.!?]+$/g)?.map((s) => s.trim()).filter(Boolean) ?? [];

  if (sentences.length < 2) {
    const words = normalized.split(/\s+/).filter(Boolean);
    if (words.length <= 60) return [normalized];

    const chunks = [];
    for (let index = 0; index < words.length; index += 55) {
      chunks.push(words.slice(index, index + 55).join(" "));
    }
    return chunks;
  }

  const groupedParagraphs = [];
  let currentParagraph = "";

  for (const sentence of sentences) {
    const candidate = currentParagraph ? `${currentParagraph} ${sentence}` : sentence;
    if (
      currentParagraph
      && candidate.length > TARGET_PARAGRAPH_LENGTH
      && currentParagraph.length >= MIN_PARAGRAPH_LENGTH
    ) {
      groupedParagraphs.push(currentParagraph);
      currentParagraph = sentence;
      continue;
    }
    currentParagraph = candidate;
  }

  if (currentParagraph) groupedParagraphs.push(currentParagraph);

  if (groupedParagraphs.length === 1 && sentences.length >= 4) {
    const sentenceChunks = [];
    for (let index = 0; index < sentences.length; index += 3) {
      sentenceChunks.push(sentences.slice(index, index + 3).join(" "));
    }
    return sentenceChunks.map((paragraph) => paragraph.trim()).filter(Boolean);
  }

  return groupedParagraphs.map((paragraph) => paragraph.trim()).filter(Boolean);
};

export const formatArticleParagraphs = (content) => {
  const text = normalizeText(content);
  if (!text) return [];

  const structuredParagraphs = splitByExistingStructure(text);
  if (structuredParagraphs.length) return structuredParagraphs;

  return splitPlainTextBlob(text);
};

export default formatArticleParagraphs;