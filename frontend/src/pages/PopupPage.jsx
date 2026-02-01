import { useState, useEffect } from "react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { ExternalLink, FileSearch, Loader2 } from "lucide-react";
import get_api from "@/config/config";

const PopupPage = () => {
  const [currentUrl, setCurrentUrl] = useState(null);
  const [isNewsPage, setIsNewsPage] = useState(false);
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [articleId, setArticleId] = useState(null);

  // Toggle states
  const [pageOverlayEnabled, setPageOverlayEnabled] = useState(false);
  const [contextMenuEnabled, setContextMenuEnabled] = useState(true);

  const [API_URL, setAPI_URL] = useState(null);

  // Get propaganda emoji based on percentage
  const getPropagandaEmoji = (percentage) => {
    if (percentage <= 30) return "✅";
    if (percentage <= 60) return "⚠️";
    return "🚨";
  };

  // Get propaganda level name
  const getPropagandaLevel = (percentage) => {
    if (percentage <= 30) return "Low";
    if (percentage <= 60) return "Moderate";
    return "High";
  };

  // Get propaganda color
  const getPropagandaColor = (percentage) => {
    if (percentage <= 30) return "bg-green-500";
    if (percentage <= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  // Get sentiment emoji based on sentiment result
  const getSentimentEmoji = (sentimentResult) => {
    if (!sentimentResult) return "😐";
    const { neutral = 0, negative = 0, positive = 0 } = sentimentResult;

    if (neutral >= 0.6) return "😐";
    if (neutral >= 0.3) return "😕";
    if (negative > positive) return "😠";
    return "🤩";
  };

  // Get sentiment level name
  const getSentimentLevel = (sentimentResult) => {
    if (!sentimentResult) return "Unknown";
    const { neutral = 0, negative = 0, positive = 0 } = sentimentResult;

    if (neutral >= 0.6) return "Neutral";
    if (neutral >= 0.3) return "Leaning";
    if (negative > positive) return "Extreme";
    return "Extreme";
  };

  // Get sentiment color based on level
  const getSentimentColor = (sentimentResult) => {
    if (!sentimentResult) return "bg-gray-500";
    const { neutral = 0, negative = 0, positive = 0 } = sentimentResult;

    if (neutral >= 0.6) return "bg-green-500";
    if (neutral >= 0.3) return "bg-yellow-500";
    return "bg-red-500";
  };

  // Get dominant sentiment percentage
  const getDominantSentimentPercentage = (sentimentResult) => {
    if (!sentimentResult) return 0;
    const { neutral = 0, negative = 0, positive = 0 } = sentimentResult;
    return Math.round(Math.max(neutral, negative, positive) * 100);
  };

  // Check if URL is likely a news article
  const isLikelyNewsUrl = (url) => {
    if (!url) return false;
    try {
      const urlObj = new URL(url);
      const pathname = urlObj.pathname.toLowerCase();

      const skipPatterns = [
        /^chrome:\/\//,
        /^chrome-extension:\/\//,
        /^about:/,
        /^file:/,
      ];

      for (const pattern of skipPatterns) {
        if (pattern.test(url)) return false;
      }

      const nonArticlePatterns = [
        /\/(login|signup|register|account|cart|checkout|search)\/?$/i,
        /\/(category|categories|tag|tags|archive)\/?$/i,
        /^\/?$/,
        /\/?(index|home|about|contact|privacy|terms)\/?$/i,
      ];

      for (const pattern of nonArticlePatterns) {
        if (pattern.test(pathname)) return false;
      }

      const pathParts = pathname.split("/").filter((p) => p.length > 0);
      return pathParts.length >= 2;
    } catch {
      return false;
    }
  };

  // Load toggle states from chrome.storage
  useEffect(() => {
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.sync.get(
        ["pageOverlayEnabled", "contextMenuEnabled"],
        (result) => {
          setPageOverlayEnabled(result.pageOverlayEnabled ?? false);
          setContextMenuEnabled(result.contextMenuEnabled ?? true);
        },
      );
    }
  }, []);

  // Initialize and fetch data
  useEffect(() => {
    const init = async () => {
      const apiUrl = await get_api();
      setAPI_URL(apiUrl);

      // Get current tab URL
      if (
        typeof chrome !== "undefined" &&
        chrome.runtime &&
        chrome.runtime.id
      ) {
        chrome.runtime.sendMessage(
          { action: "getTabUrl" },
          async (response) => {
            if (response && response.tabUrl) {
              setCurrentUrl(response.tabUrl);
              const isNews = isLikelyNewsUrl(response.tabUrl);
              setIsNewsPage(isNews);

              if (isNews && apiUrl) {
                // Check if article is analyzed - first check local cache, then API
                try {
                  // Check local cache first (chrome.storage.local)
                  const cacheKey = `analysis_${response.tabUrl}`;
                  const cached = await chrome.storage.local.get(cacheKey);
                  if (cached[cacheKey]) {
                    console.log("Found local cached analysis");
                    setAnalysisData(cached[cacheKey]);
                    setArticleId(cached[cacheKey].id);
                    setIsAnalyzed(true);
                  } else {
                    // Fall back to API
                    console.log("Checking API for cached analysis:", response.tabUrl);
                    const res = await fetch(`${apiUrl}/database/getByURL/`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ url: response.tabUrl }),
                    });

                    if (res.ok) {
                      const data = await res.json();
                      const hasAnalysis =
                        data &&
                        data.id &&
                        (data.propaganda_result?.propaganda_probability !==
                          undefined ||
                          data.sentiment_result);
                      if (hasAnalysis) {
                        setAnalysisData(data);
                        setArticleId(data.id);
                        setIsAnalyzed(true);
                        // Cache locally for faster access next time
                        await chrome.storage.local.set({ [cacheKey]: data });
                      }
                    }
                  }
                } catch (error) {
                  console.log("Could not fetch analysis data:", error);
                }
              }
              setIsLoading(false);
            } else {
              setIsLoading(false);
            }
          },
        );
      } else {
        setIsLoading(false);
      }
    };

    init();
  }, []);

  // Handle toggle changes
  const handlePageOverlayToggle = (checked) => {
    setPageOverlayEnabled(checked);
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.sync.set({ pageOverlayEnabled: checked });
    }
  };

  const handleContextMenuToggle = (checked) => {
    setContextMenuEnabled(checked);
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.sync.set({ contextMenuEnabled: checked });
    }
  };

  // Handle analyze button click
  const handleAnalyze = async () => {
    if (!currentUrl || !API_URL) return;

    setIsAnalyzing(true);

    // Notify background script
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id) {
      chrome.runtime.sendMessage({ action: "analysisStarted" });
    }

    try {
      const res = await fetch(`${API_URL}/application/new_query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: currentUrl, force: false }),
      });

      if (res.ok) {
        const data = await res.json();
        setArticleId(data.id);
        setAnalysisData(data);
        setIsAnalyzed(true);
        setIsAnalyzing(false);

        // Cache locally for persistence across popup reopens
        if (typeof chrome !== "undefined" && chrome.storage) {
          const cacheKey = `analysis_${currentUrl}`;
          chrome.storage.local.set({ [cacheKey]: data });
        }

        // Update badge if propaganda result exists
        if (
          data.propaganda_result &&
          typeof chrome !== "undefined" &&
          chrome.runtime
        ) {
          chrome.runtime.sendMessage({
            action: "propagandaResultReceived",
            propagandaProbability:
              data.propaganda_result.propaganda_probability,
            url: currentUrl,
          });
        }
      } else {
        console.error("Analysis request failed");
        setIsAnalyzing(false);
      }
    } catch (error) {
      console.error("Analysis failed:", error);
      setIsAnalyzing(false);
    }
  };

  // Handle open full analysis
  const handleOpenFullAnalysis = (id = articleId) => {
    if (!id) return;

    // Open results page in a new tab
    if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id) {
      const extensionUrl = chrome.runtime.getURL(`index.html#/results/${id}`);
      chrome.tabs.create({ url: extensionUrl });
      window.close(); // Close popup
    }
  };

  // Render indicator row
  const IndicatorRow = ({ emoji, label, level, percentage, colorClass }) => (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      <span className="text-2xl">{emoji}</span>
      <div className="flex-1">
        <div className="flex justify-between items-center mb-1">
          <span className="font-medium text-sm">{label}</span>
          <span className="text-xs text-gray-500">{level}</span>
        </div>
        <div className="flex items-center gap-2">
          <Progress
            value={percentage}
            className="h-2 flex-1"
            indicatorClassName={colorClass}
          />
          <span className="text-xs font-semibold w-10 text-right">
            {percentage}%
          </span>
        </div>
      </div>
    </div>
  );

  // Render skeleton loader
  const SkeletonLoader = () => (
    <div className="space-y-3">
      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
        <Skeleton className="h-8 w-8 rounded" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-2 w-full" />
        </div>
      </div>
      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
        <Skeleton className="h-8 w-8 rounded" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-2 w-full" />
        </div>
      </div>
    </div>
  );

  return (
    <div
      className="w-[350px] min-h-[400px] p-4 bg-white overflow-y-auto"
      style={{ width: "350px", minHeight: "400px" }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <img src="checkmate.png" alt="Checkmate" className="w-8 h-8" />
        <div>
          <h1 className="text-lg font-bold text-gray-900">Checkmate</h1>
          <p className="text-xs text-gray-500">News Bias Detector</p>
        </div>
      </div>

      {/* Main Content */}
      <Card className="mb-4">
        <CardContent className="p-3 min-h-[160px]">
          {isLoading ? (
            <SkeletonLoader />
          ) : !isNewsPage ? (
            <div className="text-center py-6">
              <FileSearch className="w-12 h-12 mx-auto text-gray-400 mb-2" />
              <p className="text-gray-600 font-medium">Not a news article</p>
              <p className="text-xs text-gray-400 mt-1">
                Navigate to a news article to analyze it
              </p>
            </div>
          ) : isAnalyzing ? (
            <div className="text-center py-11">
              <Loader2 className="w-12 h-12 mx-auto text-blue-500 mb-3 animate-spin" />
              <p className="text-gray-600 font-medium">Analyzing...</p>
              <p className="text-xs text-gray-400 mt-1">
                This might take a few moments
              </p>
            </div>
          ) : !isAnalyzed ? (
            <div className="text-center py-6">
              <FileSearch className="w-12 h-12 mx-auto text-blue-500 mb-2" />
              <p className="text-gray-600 font-medium mb-3">Ready to analyze</p>
              <Button
                onClick={handleAnalyze}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Analyze This Page
              </Button>
            </div>
          ) : (
            <div className="space-y-3 py-6">
              {/* Propaganda Indicator */}
              {analysisData?.propaganda_result?.propaganda_probability !==
                undefined && (
                <IndicatorRow
                  emoji={getPropagandaEmoji(
                    Math.round(
                      analysisData.propaganda_result.propaganda_probability *
                        100,
                    ),
                  )}
                  label="Propaganda"
                  level={getPropagandaLevel(
                    Math.round(
                      analysisData.propaganda_result.propaganda_probability *
                        100,
                    ),
                  )}
                  percentage={Math.round(
                    analysisData.propaganda_result.propaganda_probability * 100,
                  )}
                  colorClass={getPropagandaColor(
                    Math.round(
                      analysisData.propaganda_result.propaganda_probability *
                        100,
                    ),
                  )}
                />
              )}

              {/* Sentiment Indicator */}
              {analysisData?.sentiment_result && (
                <IndicatorRow
                  emoji={getSentimentEmoji(analysisData.sentiment_result)}
                  label="Sentiment"
                  level={getSentimentLevel(analysisData.sentiment_result)}
                  percentage={getDominantSentimentPercentage(
                    analysisData.sentiment_result,
                  )}
                  colorClass={getSentimentColor(analysisData.sentiment_result)}
                />
              )}

              {/* If only partial data, show skeleton for missing */}
              {!analysisData?.propaganda_result && <SkeletonLoader />}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Toggle Switches */}
      <Card className="mb-4">
        <CardContent className="p-3 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Page Overlay</p>
              <p className="text-xs text-gray-400">Highlight claims on page</p>
            </div>
            <Switch
              checked={pageOverlayEnabled}
              onCheckedChange={handlePageOverlayToggle}
              disabled={!isNewsPage}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Context Menu</p>
              <p className="text-xs text-gray-400">Right-click to fact-check</p>
            </div>
            <Switch
              checked={contextMenuEnabled}
              onCheckedChange={handleContextMenuToggle}
            />
          </div>
        </CardContent>
      </Card>

      {/* Action Button */}
      <Button
        className="w-full bg-blue-600 hover:bg-blue-700"
        onClick={() => handleOpenFullAnalysis()}
        disabled={!isAnalyzed}
      >
        <ExternalLink className="w-4 h-4 mr-2" />
        Open Full Analysis
      </Button>
    </div>
  );
};

export default PopupPage;
