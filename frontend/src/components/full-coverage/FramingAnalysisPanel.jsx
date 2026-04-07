import { useState } from "react";
import { Eye, ChevronDown } from "lucide-react";

const COVERAGE_DESCRIPTIONS = {
    left: "Left-lean outlets tend to frame headlines around systemic issues, policy impacts, and community effects. High passive voice may indicate focus on victims or structures.",
    center: "Centrist outlets typically aim for neutral framing. Balanced active/passive voice and fewer charged keywords suggest an effort to report facts without ideological emphasis.",
    right: "Right-lean outlets often emphasise individual responsibility and government accountability. High active voice may reflect a direct, attribution-focused writing style.",
};

const FramingAnalysisPanel = ({ framingDiff, linguisticFraming }) => {
    const [isOpen, setIsOpen] = useState(false);

    if (!framingDiff.left?.length && !framingDiff.center?.length && !framingDiff.right?.length &&
        !linguisticFraming.left && !linguisticFraming.center && !linguisticFraming.right) {
        return null;
    }

    return (
        <div className="mt-6 rounded-xl border border-slate-200 bg-gray-200 shadow-sm mb-12 hover:border-blue-400 transition-colors">
            {/* Accordion Header — always visible */}
            <button
                onClick={() => setIsOpen(prev => !prev)}
                className={`w-full px-6 py-4 border-b border-slate-100 flex items-start justify-between gap-4 text-left hover:bg-slate-50 transition-colors focus:outline-none ${isOpen ? 'rounded-t-xl' : 'rounded-xl'}`}
            >
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <Eye className="h-4 w-4 text-slate-500 flex-shrink-0" />
                        <h3 className="text-lg font-bold text-slate-800 tracking-tight">
                            Framing Differences in Headline
                        </h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-3">
                        Headlines reveal how each outlet frames the same story. This section analyses the
                        distinctive words each political side uses and whether coverage leans on{" "}
                        <strong className="text-slate-600">active voice</strong> (attributing clear intent to a subject)
                        or <strong className="text-slate-600">passive voice</strong> (focusing on outcomes without
                        naming the actor).
                    </p>
                </div>
                <span className="flex-shrink-0 mt-1 text-slate-400">
                    <ChevronDown
                        className="h-5 w-5 transition-transform duration-300"
                        style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0deg)" }}
                    />
                </span>
            </button>

            {/* Accordion Body — always rendered, animated via max-height */}
            <div
                style={{
                    maxHeight: isOpen ? "1000px" : "0px",
                    opacity: isOpen ? 1 : 0,
                    overflow: "hidden",
                    transition: "max-height 0.4s ease, opacity 0.3s ease",
                }}
            >
                <div className="grid grid-cols-3 divide-x divide-slate-100 bg-white rounded-b-xl overflow-hidden">
                    {[
                        { key: "left", label: "Left Coverage", headerClass: "text-blue-700 bg-blue-50", badgeClass: "bg-blue-100 text-blue-800", barColor: "bg-blue-500" },
                        { key: "center", label: "Center Coverage", headerClass: "text-purple-600 bg-purple-50", badgeClass: "bg-purple-200 text-purple-700", barColor: "bg-purple-400" },
                        { key: "right", label: "Right Coverage", headerClass: "text-red-700 bg-red-50", badgeClass: "bg-red-100 text-red-800", barColor: "bg-red-500" },
                    ].map(({ key, label, headerClass, badgeClass, barColor }) => {
                        const lf = linguisticFraming[key] || {};
                        const passivePct = lf.passive_pct ?? null;
                        const activePct = lf.active_pct ?? null;
                        const topAgents = lf.top_agents || [];

                        return (
                            <div key={key}>
                                {/* Column header */}
                                <div className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider ${headerClass}`}>
                                    {label}
                                </div>

                                {/* Interpretation note */}
                                <p className="px-4 pt-3 pb-1 text-sm text-slate-500 leading-relaxed">
                                    {COVERAGE_DESCRIPTIONS[key]}
                                </p>

                                {/* Keyword badges */}
                                <div className="px-4 pt-3 pb-2 flex flex-wrap gap-2 min-h-[60px]">
                                    {(framingDiff[key] || []).length > 0
                                        ? framingDiff[key].map((word, i) => (
                                            <span key={i} className={`inline-flex items-center justify-center px-3 py-1.5 rounded-full text-xs font-semibold leading-none ${badgeClass}`}>
                                                {word}
                                            </span>
                                        ))
                                        : <span className="text-xs text-slate-400 italic">Not enough data</span>
                                    }
                                </div>

                                {/* Active / Passive voice bar */}
                                {passivePct !== null && (
                                    <div className="px-4 pb-5 pt-2">
                                        <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                                            <span>Active <span className="font-semibold text-slate-700">{activePct}%</span></span>
                                            <span>Passive <span className="font-semibold text-slate-700">{passivePct}%</span></span>
                                        </div>
                                        <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                                            <div className={`h-full rounded-full ${barColor} opacity-70`} style={{ width: `${activePct}%` }} />
                                        </div>
                                        <p className="mt-2 text-xs text-slate-400">
                                            {activePct >= 60
                                                ? "Predominantly active voice — clear attribution of intent."
                                                : passivePct >= 60
                                                    ? "Predominantly passive voice — focus on outcomes over actors."
                                                    : "Mixed voice — balanced attribution style."}
                                        </p>
                                        {topAgents.length > 0 && (
                                            <div className="mt-2 flex flex-wrap gap-1 items-center">
                                                <span className="text-xs text-slate-400">Key agents:</span>
                                                {topAgents.map((a, i) => (
                                                    <span key={i} className="inline-flex items-center justify-center px-2 py-1 rounded bg-slate-100 text-xs font-medium text-slate-600 leading-none">{a}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default FramingAnalysisPanel;
