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
    const { neutral = 0 } = sentimentResult;

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
      const hostname = urlObj.hostname.toLowerCase();
      const pathname = urlObj.pathname.toLowerCase();
      const fullUrl = url.toLowerCase();

      // Skip browser-specific URLs
      const skipPatterns = [
        /^chrome:\/\//,
        /^chrome-extension:\/\//,
        /^about:/,
        /^file:/,
        /^edge:\/\//,
        /^moz-extension:\/\//,
      ];

      for (const pattern of skipPatterns) {
        if (pattern.test(url)) return false;
      }

      // Blocklist: domains that are definitely NOT news sites
      const nonNewsDomains = [
        // Social media
        /^(www\.)?(facebook|fb)\.com$/,
        /^(www\.)?twitter\.com$/,
        /^(www\.)?x\.com$/,
        /^(www\.)?instagram\.com$/,
        /^(www\.)?tiktok\.com$/,
        /^(www\.)?snapchat\.com$/,
        /^(www\.)?pinterest\.com$/,
        /^(www\.)?linkedin\.com$/,
        /^(www\.)?reddit\.com$/,
        /^(www\.)?discord\.(com|gg)$/,
        /^(www\.)?threads\.net$/,
        // Video/streaming platforms
        /^(www\.)?(youtube|youtu\.be)\.com$/,
        /^(www\.)?netflix\.com$/,
        /^(www\.)?hulu\.com$/,
        /^(www\.)?twitch\.tv$/,
        /^(www\.)?vimeo\.com$/,
        /^(www\.)?dailymotion\.com$/,
        /^(www\.)?disneyplus\.com$/,
        /^(www\.)?primevideo\.com$/,
        /^(www\.)?spotify\.com$/,
        // E-commerce
        /^(www\.)?amazon\.(com|co\.[a-z]+|[a-z]+)$/,
        /^(www\.)?ebay\.(com|co\.[a-z]+|[a-z]+)$/,
        /^(www\.)?aliexpress\.com$/,
        /^(www\.)?alibaba\.com$/,
        /^(www\.)?etsy\.com$/,
        /^(www\.)?shopify\.com$/,
        /^(www\.)?walmart\.com$/,
        /^(www\.)?target\.com$/,
        /^(www\.)?bestbuy\.com$/,
        /^(.*\.)?shopee\.(com|sg|my|ph|[a-z]+)$/,
        /^(www\.)?lazada\.(com|sg|my|ph|[a-z]+)$/,
        // Developer/tech platforms
        /^(www\.)?github\.com$/,
        /^(www\.)?gitlab\.com$/,
        /^(www\.)?bitbucket\.org$/,
        /^(www\.)?stackoverflow\.com$/,
        /^(www\.)?stackexchange\.com$/,
        /^(www\.)?codepen\.io$/,
        /^(www\.)?jsfiddle\.net$/,
        /^(www\.)?replit\.com$/,
        /^(www\.)?npmjs\.com$/,
        /^(www\.)?pypi\.org$/,
        /^(www\.)?vercel\.com$/,
        /^(www\.)?netlify\.com$/,
        /^(www\.)?heroku\.com$/,
        /^(www\.)?railway\.app$/,
        /^(www\.)?render\.com$/,
        // Backend/Database services
        /^(.*\.)?supabase\.(com|co|io)$/,
        /^(.*\.)?firebase\.google\.com$/,
        /^(.*\.)?firebaseio\.com$/,
        /^(www\.)?planetscale\.com$/,
        /^(www\.)?neon\.tech$/,
        /^(www\.)?mongodb\.com$/,
        /^(www\.)?redis\.io$/,
        /^(www\.)?cockroachlabs\.com$/,
        // Atlassian products
        /^(.*\.)?atlassian\.(com|net)$/,
        /^(.*\.)?jira\.com$/,
        /^(.*\.)?confluence\.(com|atlassian\.com)$/,
        /^(.*\.)?trello\.com$/,
        // Cloud platforms
        /^(.*\.)?aws\.amazon\.com$/,
        /^(.*\.)?console\.aws\.amazon\.com$/,
        /^(.*\.)?azure\.com$/,
        /^(.*\.)?portal\.azure\.com$/,
        /^(.*\.)?cloud\.google\.com$/,
        /^(.*\.)?console\.cloud\.google\.com$/,
        /^(www\.)?digitalocean\.com$/,
        /^(www\.)?linode\.com$/,
        // Documentation sites
        /^(.*\.)?readthedocs\.(io|org)$/,
        /^(.*\.)?gitbook\.io$/,
        /^(.*\.)?docs\./,
        /^(www\.)?devdocs\.io$/,
        /^(www\.)?mdn\.io$/,
        /^(.*\.)?mozilla\.org$/,
        // Productivity/tools
        /^(www\.)?google\.(com|co\.[a-z]+|[a-z]+)$/,
        /^(mail|drive|docs|sheets|calendar)\.google\.com$/,
        /^(www\.)?notion\.so$/,
        /^(www\.)?trello\.com$/,
        /^(www\.)?asana\.com$/,
        /^(www\.)?slack\.com$/,
        /^(www\.)?zoom\.us$/,
        /^(www\.)?dropbox\.com$/,
        /^(www\.)?onedrive\.live\.com$/,
        /^(www\.)?figma\.com$/,
        /^(www\.)?canva\.com$/,
        /^(www\.)?miro\.com$/,
        /^(www\.)?airtable\.com$/,
        /^(www\.)?monday\.com$/,
        /^(www\.)?clickup\.com$/,
        /^(www\.)?basecamp\.com$/,
        /^(www\.)?linear\.app$/,
        // CRM/Business tools
        /^(.*\.)?salesforce\.com$/,
        /^(.*\.)?hubspot\.com$/,
        /^(www\.)?zendesk\.com$/,
        /^(www\.)?intercom\.com$/,
        /^(www\.)?freshdesk\.com$/,
        // AI/ML platforms
        /^(www\.)?openai\.com$/,
        /^(www\.)?anthropic\.com$/,
        /^(www\.)?claude\.ai$/,
        /^(www\.)?chat\.openai\.com$/,
        /^(www\.)?huggingface\.co$/,
        /^(www\.)?kaggle\.com$/,
        /^(www\.)?colab\.research\.google\.com$/,
        // Design/creative tools
        /^(www\.)?dribbble\.com$/,
        /^(www\.)?behance\.net$/,
        /^(www\.)?adobe\.com$/,
        /^(.*\.)?adobe\.com$/,
        // Finance/banking
        /^(.*\.)?paypal\.com$/,
        /^(www\.)?stripe\.com$/,
        /^(www\.)?wise\.com$/,
        /^(www\.)?revolut\.com$/,
        // Travel/booking
        /^(www\.)?booking\.com$/,
        /^(www\.)?airbnb\.com$/,
        /^(www\.)?expedia\.com$/,
        /^(www\.)?tripadvisor\.com$/,
        /^(www\.)?kayak\.com$/,
        /^(www\.)?skyscanner\.(com|net)$/,
        // Food delivery
        /^(www\.)?ubereats\.com$/,
        /^(www\.)?doordash\.com$/,
        /^(www\.)?grubhub\.com$/,
        /^(www\.)?deliveroo\.(com|co\.[a-z]+)$/,
        /^(www\.)?foodpanda\.(com|sg|[a-z]+)$/,
        /^(www\.)?grab\.com$/,
        // Search engines
        /^(www\.)?bing\.com$/,
        /^(www\.)?duckduckgo\.com$/,
        /^(www\.)?yahoo\.com$/,
        /^search\./,
        // Other non-news
        /^(www\.)?wikipedia\.org$/,
        /^[a-z]+\.wikipedia\.org$/,
        /^(www\.)?imdb\.com$/,
        /^(www\.)?rottentomatoes\.com$/,
        /^(www\.)?goodreads\.com$/,
        /^(www\.)?quora\.com$/,
        /^(www\.)?medium\.com$/,
        /^(www\.)?substack\.com$/,
        /^(www\.)?patreon\.com$/,
        /^(www\.)?kickstarter\.com$/,
        /^(www\.)?gofundme\.com$/,
        /^localhost(:\d+)?$/,
        /^127\.0\.0\.1(:\d+)?$/,
      ];

      for (const pattern of nonNewsDomains) {
        if (pattern.test(hostname)) return false;
      }

      // Non-article URL patterns (paths that are definitely not articles)
      const nonArticlePatterns = [
        /\/(login|signin|signup|register|logout|account|profile|settings)\/?$/i,
        /\/(cart|checkout|basket|wishlist|orders?)\/?$/i,
        /\/(search|results|browse|explore)\/?$/i,
        /\/(category|categories|tag|tags|archive|archives|topics?)\/?$/i,
        /^\/?$/,  // Root path (home page)
        /\/?(index|home|about|contact|privacy|terms|faq|help|support)\/?$/i,
        /\/(products?|shop|store|buy|pricing|plans?|subscribe)\/?$/i,
        /\/(download|install|apps?)\/?$/i,
        /\/(video|videos|watch|playlist|channel|live)\/?$/i,
        /\/(photos?|images?|gallery|galleries|media)\/?$/i,
        /\/(jobs?|careers?|hiring)\/?$/i,
        /\/(auth|oauth|callback|verify|confirm)\/?$/i,
        /\/(api|graphql|webhook)\/?/i,
        /\.(jpg|jpeg|png|gif|webp|svg|pdf|mp4|mp3|zip|exe)$/i,
        // Section/category pages (single segment paths that are likely not articles)
        /^\/(news|world|politics|business|economy|sports?|entertainment|health|science|technology|tech|opinion|editorial|lifestyle|travel|food|culture|money|weather|video|live|latest|trending|popular|top-stories?)\/?$/i,
        /^\/(us|uk|asia|europe|africa|americas|middle-east|australia)\/?$/i,
        /^\/(local|national|international|global)\/?$/i,
      ];

      for (const pattern of nonArticlePatterns) {
        if (pattern.test(pathname)) return false;
      }

      // Known news domain patterns (allowlist - high confidence)
      const newsDomainsPatterns = [
        // Major international news
        /^(www\.)?(bbc\.(com|co\.uk)|cnn\.com|reuters\.com|apnews\.com)$/,
        /^(www\.)?(nytimes\.com|washingtonpost\.com|theguardian\.com)$/,
        /^(www\.)?(wsj\.com|ft\.com|economist\.com|bloomberg\.com)$/,
        /^(www\.)?(nbcnews\.com|cbsnews\.com|abcnews\.go\.com|foxnews\.com)$/,
        /^(www\.)?(npr\.org|pbs\.org|aljazeera\.com)$/,
        /^(www\.)?(usatoday\.com|latimes\.com|nypost\.com|politico\.com)$/,
        /^(www\.)?(thehill\.com|axios\.com|vox\.com|buzzfeednews\.com)$/,
        /^(www\.)?(independent\.co\.uk|telegraph\.co\.uk|dailymail\.co\.uk)$/,
        /^(www\.)?(forbes\.com|businessinsider\.com|cnbc\.com)$/,
        /^(www\.)?(huffpost\.com|huffingtonpost\.com|theatlantic\.com)$/,
        /^(www\.)?(time\.com|newsweek\.com|usnews\.com)$/,
        // Asia Pacific news
        /^(www\.)?(straitstimes\.com|channelnewsasia\.com|todayonline\.com)$/,
        /^(www\.)?(scmp\.com|asia\.nikkei\.com|japantimes\.co\.jp)$/,
        /^(www\.)?(koreaherald\.com|koreatimes\.co\.kr)$/,
        /^(www\.)?(thehindu\.com|indianexpress\.com|hindustantimes\.com)$/,
        /^(www\.)?(abc\.net\.au|news\.com\.au|smh\.com\.au)$/,
        // Tech news
        /^(www\.)?(techcrunch\.com|theverge\.com|wired\.com|arstechnica\.com)$/,
        /^(www\.)?(engadget\.com|gizmodo\.com|mashable\.com|cnet\.com)$/,
        /^(www\.)?(zdnet\.com|venturebeat\.com|techradar\.com)$/,
      ];

      // If it's a known news domain, apply less strict checks
      const isKnownNewsDomain = newsDomainsPatterns.some((pattern) =>
        pattern.test(hostname)
      );

      if (isKnownNewsDomain) {
        // For known news sites, require article-like path depth
        const pathParts = pathname.split("/").filter((p) => p.length > 0);

        // Need at least 2 path segments (e.g., /world/article-slug)
        // OR 1 segment that looks like an article slug (long with hyphens)
        if (pathParts.length >= 2) {
          return true;
        }
        if (pathParts.length === 1) {
          const slug = pathParts[0];
          // Article slugs are typically long and contain hyphens
          const looksLikeArticleSlug = slug.length > 25 && slug.includes("-");
          return looksLikeArticleSlug;
        }
        return false;
      }

      // For unknown domains, look for strong news article indicators
      const newsIndicatorPatterns = [
        // Date patterns in URL (common in news articles)
        /\/\d{4}\/\d{1,2}\/\d{1,2}\//,  // /2024/01/15/
        /\/\d{4}\/\d{1,2}\//,            // /2024/01/
        /\/\d{4}-\d{2}-\d{2}/,           // /2024-01-15
        /\/\d{8}\//,                      // /20240115/
        // News-specific path segments
        /\/(news|article|story|stories|post|posts|breaking|headlines?)\//i,
        /\/(world|politics|business|economy|sports?|entertainment|health|science|tech(nology)?|opinion|editorial)\//i,
        /\/(local|national|international|global)\//i,
        /\/(analysis|investigation|exclusive|feature|features)\//i,
        // Article ID patterns (common in news URLs)
        /\/[a-z]+-[a-z]+-[a-z]+(-[a-z]+){2,}/i,  // slug-style URLs with 5+ words
        /-\d{5,}/,  // Numeric article IDs
        /\/[a-f0-9]{8,}/i,  // Hash-style IDs
      ];

      // Check if URL contains news indicators
      const hasNewsIndicator = newsIndicatorPatterns.some(
        (pattern) => pattern.test(pathname) || pattern.test(fullUrl)
      );

      if (hasNewsIndicator) {
        return true;
      }

      // Check for news-related terms in domain name
      const newsyDomainPatterns = [
        /news/i,
        /times/i,
        /post/i,
        /herald/i,
        /tribune/i,
        /journal/i,
        /gazette/i,
        /chronicle/i,
        /daily/i,
        /report(er)?/i,
        /press/i,
        /wire/i,
        /today/i,
      ];

      const hasNewsyDomain = newsyDomainPatterns.some((pattern) =>
        pattern.test(hostname)
      );

      if (hasNewsyDomain) {
        // For domains with news-related names, require at least 2 path segments
        const pathParts = pathname.split("/").filter((p) => p.length > 0);
        return pathParts.length >= 2;
      }

      // Default: be conservative - require strong signals
      // Must have decent path depth AND look like an article URL
      const pathParts = pathname.split("/").filter((p) => p.length > 0);
      const hasArticleLikePath = pathParts.length >= 3 ||
        (pathParts.length >= 2 && pathParts.some(p => p.length > 20));  // Long slug

      return hasArticleLikePath;
    } catch {
      return false;
    }
  };

  // Load toggle states from chrome.storage
  useEffect(() => {
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.sync.get(
        ["contextMenuEnabled"],
        (result) => {
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
                // Helper to check if data has complete analysis (requires BOTH)
                const isCompleteAnalysis = (data) =>
                  data &&
                  data.id &&
                  data.propaganda_result?.propaganda_probability !== undefined &&
                  data.sentiment_result;

                // Check if article is analyzed - first check local cache, then API
                try {
                  // Check local cache first (chrome.storage.local)
                  const cacheKey = `analysis_${response.tabUrl}`;
                  const cached = await chrome.storage.local.get(cacheKey);

                  // Only use cache if it has complete analysis data
                  if (cached[cacheKey] && isCompleteAnalysis(cached[cacheKey])) {
                    console.log("Found complete cached analysis");
                    setAnalysisData(cached[cacheKey]);
                    setArticleId(cached[cacheKey].id);
                    setIsAnalyzed(true);
                    setIsLoading(false);
                    // Update badge for cached data
                    if (cached[cacheKey].propaganda_result?.propaganda_probability !== undefined) {
                      try {
                        chrome.runtime.sendMessage({
                          action: "propagandaResultReceived",
                          propagandaProbability: cached[cacheKey].propaganda_result.propaganda_probability,
                          url: response.tabUrl,
                        });
                      } catch (e) {
                        console.log("Could not update badge from cache:", e);
                      }
                    }
                  } else {
                    // Clear incomplete cache if exists
                    if (cached[cacheKey]) {
                      console.log("Clearing incomplete cached data");
                      await chrome.storage.local.remove(cacheKey);
                    }

                    // Show UI immediately - don't block on API check
                    setIsLoading(false);

                    // Check API in background for previously analyzed articles
                    fetch(`${apiUrl}/application/new_query`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ url: response.tabUrl, force: false }),
                    })
                      .then((res) => res.ok ? res.json() : null)
                      .then((data) => {
                        if (data && isCompleteAnalysis(data)) {
                          console.log("Found existing analysis from API");
                          setAnalysisData(data);
                          setArticleId(data.id);
                          setIsAnalyzed(true);
                          // Cache locally for faster access next time
                          chrome.storage.local.set({ [cacheKey]: data });
                          // Update badge
                          if (data.propaganda_result?.propaganda_probability !== undefined) {
                            try {
                              chrome.runtime.sendMessage({
                                action: "propagandaResultReceived",
                                propagandaProbability: data.propaganda_result.propaganda_probability,
                                url: response.tabUrl,
                              });
                            } catch (e) {
                              console.log("Could not update badge from API:", e);
                            }
                          }
                        }
                      })
                      .catch((err) => console.log("Background API check failed:", err));
                  }
                } catch (error) {
                  console.log("Could not fetch analysis data:", error);
                  setIsLoading(false);
                }
              } else {
                setIsLoading(false);
              }
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
  const handleContextMenuToggle = (checked) => {
    setContextMenuEnabled(checked);
    if (typeof chrome !== "undefined" && chrome.storage) {
      chrome.storage.sync.set({ contextMenuEnabled: checked });
    }
  };

  // Check if response has complete analysis results (requires BOTH propaganda AND sentiment)
  const hasCompleteAnalysis = (data) => {
    return (
      data &&
      data.id &&
      data.propaganda_result?.propaganda_probability !== undefined &&
      data.sentiment_result
    );
  };

  // Poll for analysis results using the new_query endpoint (returns cached if complete)
  const pollForResults = async (url, maxAttempts = 30, interval = 2000) => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        console.log(`Polling attempt ${attempt + 1}/${maxAttempts}...`);
        const res = await fetch(`${API_URL}/application/new_query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, force: false }),
        });
        if (res.ok) {
          const data = await res.json();
          if (hasCompleteAnalysis(data)) {
            console.log("Found complete analysis on poll attempt", attempt + 1);
            return data;
          }
        }
      } catch (error) {
        console.log("Polling attempt failed:", error);
      }
      // Wait before next attempt
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
    return null;
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
        let data = await res.json();
        setArticleId(data.id);

        // Check if we have complete analysis results
        if (hasCompleteAnalysis(data)) {
          setAnalysisData(data);
          setIsAnalyzed(true);
          setIsAnalyzing(false);
        } else if (data.id) {
          // Analysis is still processing, poll for results
          console.log("Analysis in progress, polling for results...");
          const completeData = await pollForResults(currentUrl);
          if (completeData) {
            data = completeData;
            setAnalysisData(data);
            setIsAnalyzed(true);
          } else {
            console.error("Analysis timed out");
          }
          setIsAnalyzing(false);
        } else {
          setIsAnalyzing(false);
        }

        // Cache locally for persistence across popup reopens (only if we have results)
        if (hasCompleteAnalysis(data) && typeof chrome !== "undefined" && chrome.storage) {
          const cacheKey = `analysis_${currentUrl}`;
          chrome.storage.local.set({ [cacheKey]: data });
        }

        // Cache locally for persistence across popup reopens
        if (typeof chrome !== "undefined" && chrome.storage) {
          const cacheKey = `analysis_${currentUrl}`;
          chrome.storage.local.set({ [cacheKey]: data });
        }

        // Update badge if propaganda result exists
        if (
          data.propaganda_result &&
          typeof chrome !== "undefined" &&
          chrome.runtime &&
          chrome.runtime.id
        ) {
          try {
            chrome.runtime.sendMessage({
              action: "propagandaResultReceived",
              propagandaProbability:
                data.propaganda_result.propaganda_probability,
              url: currentUrl,
            });
            console.log("Badge update message sent successfully");
          } catch (error) {
            console.error("Failed to send badge update message:", error);
          }
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
            <div className="text-center py-11">
              <Loader2 className="w-8 h-8 mx-auto text-gray-400 mb-2 animate-spin" />
              <p className="text-sm text-gray-500">Checking page...</p>
            </div>
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
