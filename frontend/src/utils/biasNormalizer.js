/**
 * Normalizes all bias label variants to the canonical "lean" form.
 * Handles: "leaning-left", "leaning left", "lean-left", "lean left" → "lean-left"
 * Storage is never modified — normalization happens only at display time.
 */
export const normalizeBias = (raw) => {
  const s = (raw || "").toLowerCase().trim().replace(/_/g, "-").replace(/\s+/g, "-");
  if (s === "left")                              return "left";
  if (s === "leaning-left"  || s === "lean-left")  return "lean-left";
  if (s === "center" || s === "centre" || s === "neutral" || s === "balanced") return "center";
  if (s === "leaning-right" || s === "lean-right") return "lean-right";
  if (s === "right")                             return "right";
  return s || "unknown";
};

export const BIAS_LABELS = {
  "left":       "Left",
  "lean-left":  "Lean Left",
  "center":     "Center",
  "lean-right": "Lean Right",
  "right":      "Right",
};

export const getBiasLabel = (raw) => {
  const key = normalizeBias(raw);
  return BIAS_LABELS[key] ?? raw ?? "Unknown";
};