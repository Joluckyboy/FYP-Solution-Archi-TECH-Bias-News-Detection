import { Eye } from "lucide-react";

const FramingAnalysisPanel = ({ framingDiff, linguisticFraming }) => {
    if (!framingDiff.left?.length && !framingDiff.center?.length && !framingDiff.right?.length &&
        !linguisticFraming.left && !linguisticFraming.center && !linguisticFraming.right) {
        return null;
    }

    return (
        <div className="mt-6 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden mb-12">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
                <Eye className="h-4 w-4 text-slate-500" />
                <h3 className="font-semibold text-slate-700">Framing Differences in Headline</h3>
                <span className="text-xs text-slate-400 ml-1">— Note: Active voice attributes clear intent to a subject, while passive voice focuses on the result.</span>
            </div>
            <div className="grid grid-cols-3 divide-x divide-slate-100">
                {[
                    { key: "left", label: "Left Coverage", headerClass: "text-blue-700 bg-blue-100", badgeClass: "bg-blue-100 text-blue-800", barColor: "bg-blue-500" },
                    { key: "center", label: "Center Coverage", headerClass: "text-purple-600 bg-purple-100", badgeClass: "bg-purple-200 text-purple-700", barColor: "bg-purple-400" },
                    { key: "right", label: "Right Coverage", headerClass: "text-red-700 bg-red-100", badgeClass: "bg-red-100 text-red-800", barColor: "bg-red-500" },
                ].map(({ key, label, headerClass, badgeClass, barColor }) => {
                    const lf = linguisticFraming[key] || {};
                    const passivePct = lf.passive_pct ?? null;
                    const activePct = lf.active_pct ?? null;
                    const topAgents = lf.top_agents || [];
                    return (
                        <div key={key}>
                            <div className={`px-4 py-2 text-xs font-bold uppercase tracking-wider ${headerClass}`}>{label}</div>
                            {/* Keyword badges */}
                            <div className="px-4 pt-4 pb-2 flex flex-wrap gap-2 min-h-[60px]">
                                {(framingDiff[key] || []).length > 0
                                    ? framingDiff[key].map((word, i) => (
                                        <span key={i} className={`px-2.5 py-1 rounded-full text-xs font-semibold ${badgeClass}`}>{word}</span>
                                    ))
                                    : <span className="text-xs text-slate-400 italic">Not enough data</span>
                                }
                            </div>
                            {/* Passive / Active voice bar */}
                            {passivePct !== null && (
                                <div className="px-4 pb-4 pt-1">
                                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                                        <span>Active <span className="font-semibold">{activePct}%</span></span>
                                        <span>Passive <span className="font-semibold">{passivePct}%</span></span>
                                    </div>
                                    <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                                        <div className={`h-full rounded-full ${barColor} opacity-70`} style={{ width: `${activePct}%` }} />
                                    </div>
                                    {topAgents.length > 0 && (
                                        <div className="mt-2 flex flex-wrap gap-1 items-center">
                                            <span className="text-xs text-slate-400">Agents:</span>
                                            {topAgents.map((a, i) => (
                                                <span key={i} className="text-xs font-medium text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">{a}</span>
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
    );
};

export default FramingAnalysisPanel;
