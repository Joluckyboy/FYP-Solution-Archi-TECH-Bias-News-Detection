const TECHNIQUE_COLORS = {
  "Loaded_Language":           { bg: "#fef08a", color: "#854d0e", label: "Loaded Language",           def: "Uses emotionally charged words to influence feelings" },
  "Name_Calling,Labeling":     { bg: "#fca5a5", color: "#991b1b", label: "Name Calling",              def: "Attaches a negative label to provoke emotional reaction" },
  "Flag-Waving":               { bg: "#bfdbfe", color: "#1e40af", label: "Flag Waving",               def: "Appeals to national pride or group identity" },
  "Doubt":                     { bg: "#fcd34d", color: "#92400e", label: "Doubt",                     def: "Questions credibility without evidence" },
  "Appeal_to_fear-prejudice":  { bg: "#e9d5ff", color: "#6b21a8", label: "Appeal to Fear",            def: "Builds support by instilling fear or prejudice" },
  "Repetition":                { bg: "#99f6e4", color: "#0f766e", label: "Repetition",                def: "Repeats a message to bypass critical thinking" },
  "Exaggeration,Minimisation": { bg: "#fed7aa", color: "#c2410c", label: "Exaggeration / Minimisation", def: "Overstates or understates facts to distort reality" },
  "Bandwagon":                 { bg: "#d9f99d", color: "#3f6212", label: "Bandwagon",                 def: "Implies everyone agrees to pressure conformity" },
  "Slogans":                   { bg: "#fbcfe8", color: "#9d174d", label: "Slogans",                   def: "Uses catchy phrases that oversimplify complex issues" },
};

export function getHighlightStyle(technique) {
  return TECHNIQUE_COLORS[technique] ?? { bg: "#e5e7eb", color: "#374151", label: technique, def: "An influence technique was detected." };
}

export function getLegendItems(techniques) {
  return techniques
    .map(t => TECHNIQUE_COLORS[t] ?? null)
    .filter(Boolean)
    .filter((item, index, self) =>
      index === self.findIndex(i => i.label === item.label)
    );
}