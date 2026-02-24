import { Info, EyeOff } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const DailyBriefingCard = ({ topic, enrichmentLoading }) => {
    const silentOutlets = topic?.silent_outlets || {};

    return (
        <div className="lg:col-span-2 relative overflow-hidden rounded-xl border border-slate-200 shadow-sm bg-white h-full">
            <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600" />
            <div className="p-6 md:p-8">
                <div className="flex items-center gap-2 mb-4">
                    <div className="p-2 bg-blue-50 rounded-lg">
                        <Info className="h-5 w-5 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Daily Briefing & AI Analysis</h3>
                </div>

                {/* Silent Outlets alerts */}
                {(silentOutlets.left_silent || silentOutlets.right_silent || silentOutlets.center_silent) && (
                    <div className="mb-4 space-y-2">
                        {silentOutlets.left_silent && (
                            <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                                <EyeOff className="h-4 w-4 flex-shrink-0" />
                                <span><strong>Left outlets are silent</strong> — this story has no left-leaning coverage despite significant attention elsewhere.</span>
                            </div>
                        )}
                        {silentOutlets.right_silent && (
                            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                                <EyeOff className="h-4 w-4 flex-shrink-0" />
                                <span><strong>Right outlets are silent</strong> — this story has no right-leaning coverage despite significant attention elsewhere.</span>
                            </div>
                        )}
                        {silentOutlets.center_silent && (
                            <div className="flex items-center gap-2 p-3 bg-purple-50 border border-purple-200 rounded-lg text-sm text-purple-800">
                                <EyeOff className="h-4 w-4 flex-shrink-0" />
                                <span><strong>Center outlets are silent</strong> — no centrist coverage found for this story.</span>
                            </div>
                        )}
                    </div>
                )}

                <div className="space-y-6">
                    <div>
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Event Summary</h4>
                        <div className="text-slate-900 text-lg leading-relaxed whitespace-pre-line">
                            {enrichmentLoading ? (
                                <div className="space-y-4">
                                    <Skeleton className="h-6 w-full" />
                                    <Skeleton className="h-6 w-3/4" />
                                    <Skeleton className="h-6 w-1/2" />
                                </div>
                            ) : (
                                (topic.contextual_insight || "Analysis in progress...").split(/coverage analysis:/i)[0].trim()
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DailyBriefingCard;
