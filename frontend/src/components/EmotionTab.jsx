/**
 * EmotionTab.jsx
 *
 * FIXES:
 * 1. Lower secondary emotion threshold from 0.08 → 0.04 so emotions like
 *    Disapproval (6.6%) and Annoyance (4%) appear in "How might this affect you?"
 * 2. Show up to 3 reader insights (was capped at 2 effectively)
 * 3. Verdict banner mentions top 2 non-neutral emotions when dominant is neutral
 */

import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const EMOTION_COLORS = {
  joy: "#f59e0b", love: "#ec4899", excitement: "#f97316",
  optimism: "#84cc16", admiration: "#06b6d4", approval: "#22c55e",
  neutral: "#94a3b8", curiosity: "#8b5cf6", surprise: "#14b8a6",
  fear: "#ef4444", anger: "#dc2626", sadness: "#3b82f6",
  disgust: "#78716c", disappointment: "#6b7280", annoyance: "#f87171",
  grief: "#1e3a5f", remorse: "#7c3aed", embarrassment: "#db2777",
  nervousness: "#d97706", confusion: "#64748b", disapproval: "#f43f5e",
  realization: "#0ea5e9", caring: "#10b981", relief: "#a3e635", pride: "#7c3aed",
};
const getColor = (e) => EMOTION_COLORS[(e ?? "neutral").toLowerCase()] ?? "#94a3b8";

const EMOTION_EMOJI = {
  joy: "😄", love: "❤️", excitement: "🎉", fear: "😨", anger: "😡",
  sadness: "😢", neutral: "😐", optimism: "🌟", curiosity: "🤔",
  approval: "👍", disapproval: "👎", disappointment: "😞", annoyance: "😤",
  confusion: "😕", admiration: "🤩", surprise: "😮", caring: "🤗",
  relief: "😌", realization: "💡", pride: "🦁", grief: "😭",
  remorse: "😔", embarrassment: "😳", nervousness: "😰",
};

const EMOTION_MEANING = {
  neutral:        "This article mainly presents facts without strong feelings.",
  approval:       "This article carries an overall tone of support or agreement.",
  disapproval:    "This article carries an overall tone of criticism or disagreement.",
  joy:            "This article has an overall positive and happy tone.",
  sadness:        "This article carries a sorrowful or melancholic tone.",
  anger:          "This article expresses frustration, outrage, or strong opposition.",
  fear:           "This article evokes concern, worry, or a sense of threat.",
  disgust:        "This article expresses strong disapproval or revulsion.",
  surprise:       "This article covers unexpected or shocking events.",
  curiosity:      "This article raises questions and invites readers to explore further.",
  optimism:       "This article looks forward with hope or positive expectations.",
  disappointment: "This article reflects unmet expectations or letdowns.",
  annoyance:      "This article reflects mild frustration or irritation.",
  excitement:     "This article covers events with high energy and enthusiasm.",
  love:           "This article expresses warmth, affection, or deep care.",
  admiration:     "This article expresses respect and high regard for its subject.",
  grief:          "This article reflects deep loss or profound sadness.",
  remorse:        "This article expresses regret or guilt.",
  confusion:      "This article deals with unclear or conflicting information.",
  caring:         "This article expresses concern and compassion for others.",
  realization:    "This article reveals new understanding or insight.",
  relief:         "This article reflects a sense of tension being resolved.",
  nervousness:    "This article carries an anxious or uneasy tone.",
  pride:          "This article expresses achievement or a sense of identity.",
};

const READER_IMPACT = {
  neutral:        { icon: "📰", text: "This article is written in a calm, factual tone. It is unlikely to strongly influence your emotions as you read." },
  approval:       { icon: "👍", text: "Some parts of this article may make you feel supportive or agreeable toward the people or ideas it covers." },
  disapproval:    { icon: "👎", text: "This article may leave you feeling critical or sceptical — it contains language that subtly pushes back against certain ideas or people." },
  anger:          { icon: "😡", text: "This article contains language that may stir up frustration or outrage. Strong emotional reactions can affect how critically you evaluate content." },
  fear:           { icon: "😨", text: "This article uses language that may evoke worry or a sense of threat. Check whether this fear is backed by facts before drawing conclusions." },
  sadness:        { icon: "😢", text: "This article may leave you feeling sad or heavy. Emotionally charged writing can make stories feel more serious than the evidence warrants." },
  disappointment: { icon: "😞", text: "This article expresses unmet expectations. Ask yourself: whose expectations are being discussed, and do you share them?" },
  annoyance:      { icon: "😤", text: "Some readers may feel mild irritation or frustration. Consider whether that feeling is your own or being guided by the writing." },
  curiosity:      { icon: "🤔", text: "This article raises questions that may leave you wanting to find out more — a sign of engaging, thought-provoking writing." },
  optimism:       { icon: "🌟", text: "This article has a hopeful tone. Optimistic framing can sometimes downplay real risks or challenges." },
  excitement:     { icon: "🎉", text: "This article uses energetic language. High-energy writing can make events seem more significant than they are." },
  surprise:       { icon: "😮", text: "This article covers unexpected events. Surprising framing can make stories more memorable and more likely to be believed." },
  joy:            { icon: "😄", text: "This article has a positive, uplifting tone. Be aware that positive framing can sometimes gloss over complexity." },
  admiration:     { icon: "🤩", text: "This article expresses strong admiration — it may be presenting someone in a very favourable light." },
  disgust:        { icon: "🤢", text: "This article contains language designed to provoke strong disgust — a common persuasion technique." },
  realization:    { icon: "💡", text: "This article presents new information or insight that may shift your understanding of the topic." },
};

const EMOTION_GUIDE = [
  { emoji: "😐", name: "Neutral",        desc: "Reporting facts without taking a side. Common in news articles." },
  { emoji: "👍", name: "Approval",       desc: "Someone in the article is expressing support, praise, or agreement." },
  { emoji: "👎", name: "Disapproval",    desc: "Someone is expressing criticism, rejection, or disagreement." },
  { emoji: "😡", name: "Anger",          desc: "Strong frustration or outrage — often in direct quotes." },
  { emoji: "😨", name: "Fear",           desc: "The text evokes worry or threat — common in conflict or crisis articles." },
  { emoji: "😢", name: "Sadness",        desc: "The language conveys loss, grief, or sorrow." },
  { emoji: "😄", name: "Joy",            desc: "Happiness, celebration, or positive outcomes." },
  { emoji: "🌟", name: "Optimism",       desc: "Forward-looking with hope or positive expectation." },
  { emoji: "😞", name: "Disappointment", desc: "Expectations were not met — something fell short." },
  { emoji: "😤", name: "Annoyance",      desc: "Mild irritation or frustration, less intense than anger." },
  { emoji: "💡", name: "Realization",    desc: "A new understanding or discovery is being revealed." },
  { emoji: "🤔", name: "Curiosity",      desc: "The text raises questions or invites deeper thinking." },
];

const THRESHOLD = 0.02;
// ↓ FIXED: was 0.08, which cut off Disapproval (6.6%) and Annoyance (4%)
const SECONDARY_THRESHOLD = 0.04;

function _deriveDominant(weighted_avg) {
  if (!weighted_avg || !Object.keys(weighted_avg).length) return { emotion: "neutral", score: 0 };
  const filtered = Object.entries(weighted_avg).filter(([, v]) => v >= THRESHOLD);
  if (!filtered.length) return { emotion: "neutral", score: 0 };
  const [emotion, score] = filtered.sort((a, b) => b[1] - a[1])[0];
  return { emotion, score };
}

function _buildVerdict(weighted_avg, dominant_emotion) {
  const domLower = dominant_emotion?.toLowerCase() ?? "neutral";

  const NEGATIVE_EMOTIONS = ["anger", "fear", "disgust", "disapproval", "sadness", "grief", "disappointment", "annoyance", "remorse"];
  const POSITIVE_EMOTIONS = ["joy", "love", "excitement", "optimism", "approval", "admiration", "caring", "relief", "pride"];

  if (domLower !== "neutral") {
    if (NEGATIVE_EMOTIONS.includes(domLower)) {
      return {
        style: "bg-rose-50 border-rose-300 text-rose-800",
        icon: "⚠️",
        text: `This article carries a strong ${domLower} tone (${((weighted_avg[domLower] ?? 0) * 100).toFixed(1)}%). Be aware of how this may shape your reaction to the content.`,
      };
    }
    if (POSITIVE_EMOTIONS.includes(domLower)) {
      return {
        style: "bg-green-50 border-green-300 text-green-800",
        icon: "✅",
        text: `This article carries a positive ${domLower} tone (${((weighted_avg[domLower] ?? 0) * 100).toFixed(1)}%). Positive framing can sometimes make content seem more credible than it is.`,
      };
    }
  }

  // Dominant is neutral — show top 2 secondary emotions if significant
  const secondaries = Object.entries(weighted_avg)
    .filter(([k, v]) => k !== "neutral" && v >= SECONDARY_THRESHOLD)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2);

  if (secondaries.length > 0) {
    const [secEmotion, secScore] = secondaries[0];
    const isNeg = NEGATIVE_EMOTIONS.includes(secEmotion);

    // Mention second emotion if notable
    const secondPart = secondaries.length > 1
      ? ` and ${secondaries[1][0]} (${((secondaries[1][1] ?? 0) * 100).toFixed(1)}%)`
      : "";

    return {
      style: isNeg ? "bg-amber-50 border-amber-300 text-amber-800" : "bg-blue-50 border-blue-300 text-blue-800",
      icon: isNeg ? "⚠️" : "💬",
      text: `This article is mostly neutral in tone, but contains notable ${secEmotion} (${(secScore * 100).toFixed(1)}%)${secondPart} language. This may subtly shape how you feel while reading.`,
    };
  }

  return {
    style: "bg-blue-50 border-blue-300 text-blue-800",
    icon: "📰",
    text: `This article is written in a largely objective, informational tone. Emotional language is minimal.`,
  };
}

function _findExample(emotion, sentence_emotions, section_emotions) {
  if (sentence_emotions?.length) {
    // First try: find a sentence where this emotion is dominant
    const dominant = sentence_emotions
      .filter(s => s.dominant === emotion)
      .sort((a, b) => b.score - a.score)[0];
    if (dominant?.sentence) return { text: dominant.sentence, isFull: true };

    // Second try (NEW): find a sentence where this emotion appears in top_3
    // even if it wasn't the dominant — solves the "Annoyance has no example" problem
    const inTop3 = sentence_emotions
      .filter(s =>
        Array.isArray(s.top_emotions) &&
        s.top_emotions.some(e => e.label === emotion)
      )
      .map(s => ({
        sentence: s.sentence,
        emotionScore: s.top_emotions.find(e => e.label === emotion)?.score ?? 0,
      }))
      .sort((a, b) => b.emotionScore - a.emotionScore)[0];
    if (inTop3?.sentence) return { text: inTop3.sentence, isFull: true };
  }

  // Fallback: section preview
  if (section_emotions?.length) {
    const match = section_emotions
      .filter(s => (s.dominant_emotion?.toLowerCase() ?? "") === emotion)
      .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))[0];
    if (match?.preview) return { text: match.preview, isFull: false };
  }
  return null;
}

function _buildReaderInsights(weighted_avg, dominant_emotion) {
  const insights = [];
  const domLower = dominant_emotion?.toLowerCase() ?? "neutral";
  const seen = new Set();

  // Always include dominant
  const domImpact = READER_IMPACT[domLower] ?? READER_IMPACT["neutral"];
  insights.push({ emotion: domLower, ...domImpact });
  seen.add(domLower);

  // Include ALL secondary emotions above SECONDARY_THRESHOLD (not just top 1)
  const secondaries = Object.entries(weighted_avg)
    .filter(([k, v]) => k !== domLower && v >= SECONDARY_THRESHOLD && !seen.has(k))
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3); // show up to 3 secondary emotions

  for (const [emotion] of secondaries) {
    const impact = READER_IMPACT[emotion];
    if (impact && !seen.has(emotion)) {
      insights.push({ emotion, ...impact });
      seen.add(emotion);
    }
  }

  return insights;
}

const EmotionTab = ({ emotionResult }) => {
  const [guideOpen, setGuideOpen] = useState(false);

  if (!emotionResult) return null;

  const {
    weighted_avg      = {},
    dominant_emotion: rawDominant,
    dominant_score:   rawScore,
    sentence_emotions = [],
    section_emotions  = [],
  } = emotionResult;

  const derived          = _deriveDominant(weighted_avg);
  const dominant_emotion = rawDominant ?? derived.emotion;
  const dominant_score   = rawScore    ?? derived.score;
  const domLower         = dominant_emotion?.toLowerCase() ?? "neutral";
  const domColor         = getColor(dominant_emotion);

  const chartData = Object.entries(weighted_avg)
    .filter(([, v]) => v >= THRESHOLD)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([name, value]) => ({ name, value: parseFloat((value * 100).toFixed(1)) }));

  const readerInsights = _buildReaderInsights(weighted_avg, dominant_emotion);
  const verdict        = _buildVerdict(weighted_avg, dominant_emotion);

  return (
    <div className="space-y-6">

      {/* ── 1. Verdict banner ─────────────────────────────────────────────── */}
      {verdict && (
        <div className={`rounded-lg border px-4 py-3 text-sm font-medium ${verdict.style}`}>
          {verdict.icon} {verdict.text}
        </div>
      )}

      {/* ── 2. Overall Emotional Tone ─────────────────────────────────────── */}
      <div
        className="rounded-xl border-2 p-5"
        style={{ borderColor: domColor, background: domColor + "15" }}
      >
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">
          Overall Emotional Tone
        </p>
        <div className="flex items-center gap-3 mb-3">
          <span className="text-4xl">{EMOTION_EMOJI[domLower] ?? "🎭"}</span>
          <div>
            <p className="text-2xl font-bold capitalize" style={{ color: domColor }}>
              {dominant_emotion}
            </p>
            <p className="text-sm text-gray-400">
              {((dominant_score ?? 0) * 100).toFixed(1)}% of article
            </p>
          </div>
        </div>
        {EMOTION_MEANING[domLower] && (
          <p className="text-sm text-gray-600 border-t pt-3">
            💬 {EMOTION_MEANING[domLower]}
          </p>
        )}
      </div>

      {/* ── 3. How might this article affect you? ────────────────────────── */}
      {readerInsights.length > 0 && (
        <div>
          <p className="text-sm font-semibold mb-1 text-gray-600">
            How might this article affect you?
          </p>
          <p className="text-xs text-gray-400 mb-3">
            Based on the emotional language detected, here's what to be aware of as a reader.
          </p>

          <div className="flex flex-col gap-3">
            {readerInsights.map(({ emotion, icon, text }) => {
              const color   = getColor(emotion);
              const example = _findExample(emotion, sentence_emotions, section_emotions);

              return (
                <div
                  key={emotion}
                  className="rounded-xl border-2 p-4"
                  style={{ borderColor: color + "66", background: color + "0f" }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{icon}</span>
                    <span className="text-xs font-bold uppercase tracking-wide capitalize" style={{ color }}>
                      {emotion}
                    </span>
                    {/* Show percentage for non-dominant emotions so user understands scale */}
                    {emotion !== domLower && weighted_avg[emotion] !== undefined && (
                      <span className="text-[10px] text-gray-400 ml-auto">
                        {((weighted_avg[emotion] ?? 0) * 100).toFixed(1)}% of article
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-gray-700 mb-3">{text}</p>

                  {example && emotion !== "neutral" && (
                    <div className="border-l-4 pl-3 py-1" style={{ borderColor: color }}>
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-1">
                        Example from this article
                      </p>
                      <p className="text-xs text-gray-600 italic">"{example.text}"</p>
                      {!example.isFull && (
                        <p className="text-[10px] text-gray-400 mt-1">(section preview)</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 4. Emotion Breakdown ─────────────────────────────────────────── */}
      {chartData.length > 0 && (
        <div>
          <p className="text-sm font-semibold mb-1 text-gray-600">Emotion Breakdown</p>
          <div className="flex items-center gap-1.5 mb-3">
            <p className="text-xs text-gray-400">
              How strongly each emotion appears across the whole article.
            </p>
            <span className="relative group inline-flex items-center shrink-0 cursor-help">
              <span className="text-[10px] text-gray-500 bg-gray-100 rounded-full w-[16px] h-[16px] inline-flex items-center justify-center border border-gray-300 font-bold select-none">?</span>
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 leading-relaxed shadow-lg">
                These scores don't add up to 100%. Each sentence is scored on all emotions independently — a sentence can be 70% neutral and 24% approving simultaneously. The bars show emotional strength, not proportional slices.
                <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
              </span>
            </span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 16, right: 40 }}>
              <XAxis type="number" unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }}
                tickFormatter={v => v.charAt(0).toUpperCase() + v.slice(1)} />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const { name, value } = payload[0];
                  return (
                    <div style={{
                      background: "white",
                      border: "1px solid #e5e7eb",
                      borderRadius: 6,
                      padding: "6px 10px",
                      fontSize: 12,
                    }}>
                      <p style={{ margin: 0, fontWeight: 500, color: "#374151", textTransform: "capitalize" }}>
                        {name}
                      </p>
                      <p style={{ margin: 0, color: "#6b7280" }}>
                        {Number(value).toFixed(1)}%
                      </p>
                    </div>
                  );
                }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map(e => <Cell key={e.name} fill={getColor(e.name)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-50 hover:bg-gray-100 text-sm font-medium text-gray-600 transition-colors"
              onClick={() => setGuideOpen(!guideOpen)}
            >
              <span>📘 What do these emotions mean?</span>
              <span className="text-gray-400">{guideOpen ? "▲" : "▼"}</span>
            </button>
            {guideOpen && (
              <div className="px-4 py-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                {EMOTION_GUIDE.map(({ emoji, name, desc }) => (
                  <div key={name} className="flex items-start gap-2 text-xs text-gray-600">
                    <span className="text-base shrink-0">{emoji}</span>
                    <span><strong>{name}:</strong> {desc}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EmotionTab;