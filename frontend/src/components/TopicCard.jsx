import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Loader2, Zap } from "lucide-react";
import get_api from "@/config/config";
import axios from "axios";

// Domains known to block cross-origin image loads with 406
const BLOCKED_IMAGE_DOMAINS = [
    "s.yimg.com", "reuters.com", "reutersmedia.net",
    "usatoday.com", "gannett-cdn.com", "washingtonpost.com",
    "apnews.com", "nytimes.com", "wsj.com",
    "ftimg.net", "gettyimages.com", "npr.brightspotcdn.com",
    "media.cnn.com", "static.foxnews.com"
];

const isBlockedImage = (url) =>
    url && BLOCKED_IMAGE_DOMAINS.some((d) => url.toLowerCase().includes(d));

const TopicCard = ({ topic }) => {
    const { id, title, image, allImages, sourceCount, biasDistribution, frontUrl } = topic;
    const navigate = useNavigate();

    const rawImages = allImages?.length > 0 ? allImages : (image ? [image] : []);

    // Proactively proxy known blocked domains to avoid the initial 406 error
    const imagesList = rawImages.map((url) => {
        if (!url) return url;
        // Don't double-proxy
        if (url.includes('wsrv.nl')) return url;
        return isBlockedImage(url) ? `https://wsrv.nl/?url=${encodeURIComponent(url)}` : url;
    });

    const [imageIndex, setImageIndex] = useState(0);

    const currentImage = imagesList[imageIndex] || null;
    const hasImage = !!currentImage && currentImage.startsWith("http") && !currentImage.includes("placehold.co");

    const [analyzing, setAnalyzing] = useState(false);
    const [analyseError, setAnalyseError] = useState(null);

    // Support canonical and legacy bias keys so percentages stay correct during migrations.
    const getBiasValue = (...keys) => {
        for (const key of keys) {
            const value = Number(biasDistribution?.[key]);
            if (!Number.isNaN(value)) return value;
        }
        return 0;
    };

    const left = getBiasValue("left");
    const leanLeft = getBiasValue("lean-left", "lean_left", "leaning-left", "leaning_left");
    const center = getBiasValue("center", "centre");
    const leanRight = getBiasValue("lean-right", "lean_right", "leaning-right", "leaning_right");
    const right = getBiasValue("right");

    // Calculate total for percentages
    const total = left + leanLeft + center + leanRight + right;
    const leftPct = total > 0 ? ((left + leanLeft) / total) * 100 : 0;
    const centerPct = total > 0 ? (center / total) * 100 : 0;
    const rightPct = total > 0 ? ((right + leanRight) / total) * 100 : 0;

    const handleAnalyse = async () => {
        if (!frontUrl) return;
        setAnalyzing(true);
        setAnalyseError(null);
        try {
            const API_URL = await get_api();
            const res = await axios.post(`${API_URL}/application/new_query`, {
                url: frontUrl,
                force: false,
            });
            navigate(`/results/${res.data.id}?redirect=false`, {
                state: { articleUrl: frontUrl },
            });
        } catch (err) {
            console.error("Analyse failed:", err);
            setAnalyseError("Failed to analyse. Please try again.");
            setAnalyzing(false);
        }
    };

    return (
        <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-300 flex flex-col h-full border-none shadow-md">
            {/* Image Section */}
            <div className="relative h-48 w-full overflow-hidden cursor-pointer" onClick={() => navigate(`/full-coverage/${id}`)}>
                {hasImage ? (
                    <img
                        key={currentImage}
                        referrerPolicy="no-referrer"
                        src={currentImage}
                        alt={title}
                        className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                        onError={(e) => {
                            if (imageIndex < imagesList.length - 1) {
                                setImageIndex(prev => prev + 1);
                            } else {
                                e.target.style.display = "none";
                                e.target.parentNode.classList.add("bg-gradient-to-br", "from-gray-700", "to-gray-900");
                            }
                        }}
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-gray-700 to-gray-900" />
                )}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                    <h3 className="text-white font-bold text-lg leading-tight line-clamp-2 drop-shadow-md">
                        {title}
                    </h3>
                </div>
            </div>

            <CardContent className="p-4 flex-grow">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                        {sourceCount} Sources
                    </span>
                </div>

                {/* Bias Bar Chart */}
                <div className="mt-2">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1 font-semibold">
                        <span className="text-blue-600">Left {Math.round(leftPct)}%</span>
                        <span className="text-purple-500">Center {Math.round(centerPct)}%</span>
                        <span className="text-red-600">Right {Math.round(rightPct)}%</span>
                    </div>

                    <div className="h-3 w-full flex rounded-full overflow-hidden bg-gray-100">
                        <div className="h-full bg-blue-300 first:rounded-l-full relative group" style={{ width: `${leftPct}%` }} />
                        <div className="h-full bg-purple-200 relative group" style={{ width: `${centerPct}%` }} />
                        <div className="h-full bg-red-300 last:rounded-r-full relative group" style={{ width: `${rightPct}%` }} />
                    </div>
                </div>
            </CardContent>

            <CardFooter className="p-4 pt-0 flex flex-col gap-2">
                <div className="flex gap-2 w-full">
                    {/* View Full Coverage */}
                    <button
                        className="flex-1 py-2 border border-slate-400 hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-md transition-colors"
                        onClick={() => navigate(`/full-coverage/${id}`)}
                    >
                        View Full Coverage
                    </button>

                    {/* Analyse Top Article */}
                    {frontUrl ? (
                        <button
                            className="flex-1 py-2 flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-md transition-colors"
                            onClick={handleAnalyse}
                            disabled={analyzing}
                        >
                            {analyzing ? (
                                <>
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    Analysing…
                                </>
                            ) : (
                                <>
                                    Analyse Top Article
                                </>
                            )}
                        </button>
                    ) : (
                        <button
                            className="flex-1 py-2 flex items-center justify-center gap-1.5 bg-blue-200 text-blue-400 text-sm font-medium rounded-md cursor-not-allowed"
                            disabled
                            title="No article URL available"
                        >
                            <Zap className="h-3.5 w-3.5" />
                            Analyse
                        </button>
                    )}
                </div>

                {analyseError && (
                    <p className="text-xs text-red-500 text-center">{analyseError}</p>
                )}
            </CardFooter>
        </Card>
    );
};

export default TopicCard;
