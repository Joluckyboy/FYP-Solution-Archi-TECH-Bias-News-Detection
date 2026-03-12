import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Loader2, Zap } from "lucide-react";
import get_api from "@/config/config";
import axios from "axios";

const TopicCard = ({ topic }) => {
    const { id, title, image, allImages, sourceCount, biasDistribution, frontUrl } = topic;
    const navigate = useNavigate();
    
    const imagesList = allImages?.length > 0 ? allImages : (image ? [image] : []);
    const [imageIndex, setImageIndex] = useState(0);
    const [triedProxy, setTriedProxy] = useState(false);
    
    const currentImage = imagesList[imageIndex] || null;
    const hasImage = !!currentImage && currentImage.startsWith("http");

    const [analyzing, setAnalyzing] = useState(false);
    const [analyzeError, setAnalyzeError] = useState(null);

    // Calculate total for percentages
    const total = biasDistribution.left + biasDistribution.leaning_left + biasDistribution.center + biasDistribution.leaning_right + biasDistribution.right;
    const leftPct = total > 0 ? ((biasDistribution.left + biasDistribution.leaning_left) / total) * 100 : 0;
    const centerPct = total > 0 ? (biasDistribution.center / total) * 100 : 0;
    const rightPct = total > 0 ? ((biasDistribution.right + biasDistribution.leaning_right) / total) * 100 : 0;

    const handleAnalyze = async () => {
        if (!frontUrl) return;
        setAnalyzing(true);
        setAnalyzeError(null);
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
            console.error("Analyze failed:", err);
            setAnalyzeError("Failed to analyse. Please try again.");
            setAnalyzing(false);
        }
    };

    return (
        <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-300 flex flex-col h-full border-none shadow-md">
            {/* Image Section */}
            <div className="relative h-48 w-full overflow-hidden cursor-pointer" onClick={() => navigate(`/full-coverage/${id}`)}>
                {hasImage ? (
                    <img
                        src={triedProxy ? `https://wsrv.nl/?url=${encodeURIComponent(currentImage)}` : currentImage}
                        alt={title}
                        className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                        onError={(e) => { 
                            if (!triedProxy) {
                                setTriedProxy(true);
                            } else {
                                if (imageIndex < imagesList.length - 1) {
                                    setTriedProxy(false);
                                    setImageIndex(prev => prev + 1);
                                } else {
                                    e.target.style.display = "none"; 
                                    e.target.parentNode.classList.add("bg-gradient-to-br", "from-gray-700", "to-gray-900"); 
                                }
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
                        <span className="text-blue-500">Left {Math.round(leftPct)}%</span>
                        <span className="text-purple-500">Center {Math.round(centerPct)}%</span>
                        <span className="text-red-500">Right {Math.round(rightPct)}%</span>
                    </div>

                    <div className="h-3 w-full flex rounded-full overflow-hidden bg-gray-100">
                        <div className="h-full bg-blue-400 first:rounded-l-full relative group" style={{ width: `${leftPct}%` }} />
                        <div className="h-full bg-purple-500 relative group" style={{ width: `${centerPct}%` }} />
                        <div className="h-full bg-red-400 last:rounded-r-full relative group" style={{ width: `${rightPct}%` }} />
                    </div>
                </div>
            </CardContent>

            <CardFooter className="p-4 pt-0 flex flex-col gap-2">
                <div className="flex gap-2 w-full">
                    {/* View Full Coverage */}
                    <button
                        className="flex-1 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-md transition-colors"
                        onClick={() => navigate(`/full-coverage/${id}`)}
                    >
                        View Full Coverage
                    </button>

                    {/* Analyse Top Article */}
                    {frontUrl ? (
                        <button
                            className="flex-1 py-2 flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-md transition-colors"
                            onClick={handleAnalyze}
                            disabled={analyzing}
                        >
                            {analyzing ? (
                                <>
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    Analysing…
                                </>
                            ) : (
                                <>
                                    <Zap className="h-3.5 w-3.5" />
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

                {analyzeError && (
                    <p className="text-xs text-red-500 text-center">{analyzeError}</p>
                )}
            </CardFooter>
        </Card>
    );
};

export default TopicCard;
