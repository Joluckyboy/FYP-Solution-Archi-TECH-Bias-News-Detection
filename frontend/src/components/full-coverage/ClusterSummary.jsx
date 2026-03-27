import { Info, EyeOff, Sparkles } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Parses a text string that may contain:
 *  - Bullet lines:  "- **Header**: rest of text"  or  "- text"
 *  - Bold inline:   "**some text**"
 * Returns an array of React-renderable elements.
 */
const parseInsightText = (text) => {
    if (!text) return null;

    const lines = text.split("\n").filter(l => l.trim() !== "");

    return lines.map((line, idx) => {
        const trimmed = line.trim();

        // Detect bullet lines starting with "- "
        const isBullet = trimmed.startsWith("- ");
        const content = isBullet ? trimmed.slice(2) : trimmed;

        // Parse inline **bold** markers
        const parseBold = (str) => {
            const parts = str.split(/\*\*(.*?)\*\*/g);
            return parts.map((part, i) =>
                i % 2 === 1
                    ? <strong key={i} className="font-semibold text-slate-900">{part}</strong>
                    : <span key={i}>{part}</span>
            );
        };

        if (isBullet) {
            // Check if bullet has a "**Header**: description" pattern
            const headerMatch = content.match(/^\*\*(.*?)\*\*[:：](.*)/s);
            if (headerMatch) {
                const [, heading, rest] = headerMatch;
                return (
                    <li key={idx} className="flex gap-3">
                        <span className="mt-1.5 flex-shrink-0 h-2 w-2 rounded-full bg-slate-700" />
                        <span className="text-base text-slate-700 leading-relaxed">
                            <strong className="font-semibold text-slate-900 block mb-0.5">{heading}</strong>
                            {parseBold(rest.trim())}
                        </span>
                    </li>
                );
            }
            return (
                <li key={idx} className="flex gap-3">
                    <span className="mt-1.5 flex-shrink-0 h-2 w-2 rounded-full bg-slate-700" />
                    <span className="text-base text-slate-700 leading-relaxed">{parseBold(content)}</span>
                </li>
            );
        }

        // Non-bullet paragraph
        return (
            <p key={idx} className="text-base text-slate-700 leading-relaxed py-1">
                {parseBold(content)}
            </p>
        );
    });
};

const ClusterSummary = ({ topic, enrichmentLoading }) => {
    const silentOutlets = topic?.silent_outlets || {};

    const rawInsight = (topic?.contextual_insight || "")
        .split(/coverage analysis:/i)[0]
        .trim();

    return (
        <div className="lg:col-span-2 rounded-xl border border-slate-200 shadow-sm bg-white h-full overflow-hidden">
            {/* Slim accent bar */}
            <div className="h-1 w-full bg-indigo-500" />

            <div className="p-5 md:p-6">
                {/* Header */}
                <div className="flex items-center gap-2 mb-4">
                    <div className="p-2 bg-indigo-50 rounded-lg">
                        <Info className="h-5 w-5 text-indigo-600" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-800 tracking-tight">
                        Summary of this News Cluster
                    </h3>
                    <span className="ml-1 inline-flex items-center gap-1 rounded-full bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 text-sm font-medium text-indigo-600">
                        <Sparkles className="h-3 w-3" /> AI Generated
                    </span>
                </div>

                {/* Silent Outlets alerts */}
                {(silentOutlets.left_silent || silentOutlets.right_silent || silentOutlets.center_silent) && (
                    <div className="mb-4 space-y-2">
                        {silentOutlets.left_silent && (
                            <div className="flex items-start gap-2.5 p-3 bg-blue-200 border border-blue-300 rounded-lg text-base text-blue-800">
                                <EyeOff className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                <span><strong>Left outlets are silent</strong> — this story has no left-leaning coverage despite significant attention elsewhere.</span>
                            </div>
                        )}
                        {silentOutlets.right_silent && (
                            <div className="flex items-start gap-2.5 p-3 bg-red-200 border border-red-300 rounded-lg text-base text-red-800">
                                <EyeOff className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                <span><strong>Right outlets are silent</strong> — this story has no right-leaning coverage despite significant attention elsewhere.</span>
                            </div>
                        )}
                        {silentOutlets.center_silent && (
                            <div className="flex items-start gap-2.5 p-3 bg-purple-100 border border-purple-200 rounded-lg text-base text-purple-800">
                                <EyeOff className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                <span><strong>Center outlets are silent</strong> — no centrist coverage found for this story.</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Body */}
                {enrichmentLoading ? (
                    <div className="space-y-3">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-11/12" />
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-5/6" />
                    </div>
                ) : rawInsight ? (
                    <ul className="list-none space-y-2">
                        {parseInsightText(rawInsight)}
                    </ul>
                ) : (
                    <p className="text-base text-slate-400 italic">Analysis in progress…</p>
                )}

                {/* Disclaimer */}
                <p className="mt-4 text-sm text-slate-400 italic flex items-center gap-1.5">
                    <span>✦</span>
                    This summary was generated by AI and may not reflect the full context of the story.
                </p>
            </div>
        </div>
    );
};

export default ClusterSummary;
