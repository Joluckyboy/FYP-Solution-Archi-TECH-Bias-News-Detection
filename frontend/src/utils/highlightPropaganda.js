const TECHNIQUE_COLORS = {
  "Loaded_Language":           { bg: "#fef08a", color: "#854d0e", label: "Loaded Language",              def: "Uses emotionally charged words to influence feelings" },
  "Name_Calling,Labeling":     { bg: "#fca5a5", color: "#991b1b", label: "Name Calling",                 def: "Attaches a negative label to provoke emotional reaction" },
  "Flag-Waving":               { bg: "#bfdbfe", color: "#1e40af", label: "Flag Waving",                  def: "Appeals to national pride or group identity" },
  "Doubt":                     { bg: "#f59e0b", color: "#451a03", label: "Doubt",                        def: "Questions credibility without evidence" },
  "Appeal_to_fear-prejudice":  { bg: "#e9d5ff", color: "#6b21a8", label: "Appeal to Fear",               def: "Builds support by instilling fear or prejudice" },
  "Repetition":                { bg: "#99f6e4", color: "#0f766e", label: "Repetition",                   def: "Repeats a message to bypass critical thinking" },
  "Exaggeration,Minimisation": { bg: "#fed7aa", color: "#c2410c", label: "Exaggeration / Minimisation",  def: "Overstates or understates facts to distort reality" },
  "Bandwagon":                 { bg: "#d9f99d", color: "#3f6212", label: "Bandwagon",                    def: "Implies everyone agrees to pressure conformity" },
  "Slogans":                   { bg: "#fbcfe8", color: "#9d174d", label: "Slogans",                      def: "Uses catchy phrases that oversimplify complex issues" },
  "Causal_Oversimplification":                   { bg: "#fb923c", color: "#7c2d12", label: "Causal Oversimplification",    def: "Reduces a complex issue to a single cause, ignoring nuance" },
  "Reductio_ad_hitlerum":                        { bg: "#f43f5e", color: "#881337", label: "Reductio ad Hitlerum",         def: "Discredits an idea by associating it with an extreme figure" },
  "Obfuscation,Intentional_Vagueness,Confusion": { bg: "#a78bfa", color: "#3b0764", label: "Obfuscation / Vagueness",     def: "Uses unclear language to hide true intent" },
  "Appeal_to_Authority":                         { bg: "#67e8f9", color: "#164e63", label: "Appeal to Authority",         def: "Cites an authority to validate a claim without expertise" },
  "Black-and-White_Fallacy":                     { bg: "#1d4ed8", color: "#eff6ff", label: "Black & White Fallacy",       def: "Presents only two extreme options when others exist" },
  "Thought-terminating_Cliches":                 { bg: "#4ade80", color: "#14532d", label: "Thought-terminating Clichés", def: "Uses familiar phrases to shut down debate" },
  "Red_Herring":                                 { bg: "#dc2626", color: "#fff1f2", label: "Red Herring",                 def: "Introduces irrelevant information to distract from the issue" },
  "Straw_Men":                                   { bg: "#e879f9", color: "#701a75", label: "Straw Men",                   def: "Misrepresents an opponent's argument to make it easier to attack" },
  "Whataboutism":                                { bg: "#818cf8", color: "#1e1b4b", label: "Whataboutism",                def: "Deflects criticism by pointing to a different issue" },
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