import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
// import API_URL from "@/config/config";
import { isNonNewsDomain, isYouTubeUrl } from "@/utils/newsURLClassifier";
import get_api, { get_analyzer } from "@/config/config";
import BiasLabelGuide from "@/components/BiasLabelGuide";
import TrendingKeywords from "@/components/TrendingKeywords";
import TopicOutletBias from "@/components/TopicOutletBias";
import TopicFeed from "@/components/TopicFeed";
import { Search } from "lucide-react";

import { CustomInput } from "@/components/ui/custom-input";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { BadgeCheck, Scale, AlertCircle, Gauge, SmilePlus, Landmark } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";

import axios from "axios";

let API_URL = null;

const LandingPage = () => {
  let navigate = useNavigate();
  const [articleURL, setArticleURL] = useState("");
  const [isMobile, setIsMobile] = useState(false);
  const [error, setError] = useState(false);
  const [nonNewsError, setNonNewsError] = useState(false);
  const [youtubeError, setYoutubeError] = useState(false); // ← ADD
  const [forceReanalyze] = useState(false);

  // ── Topics state (lifted here so filter pills can share it) ──────────────
  const [topics, setTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [topicsError, setTopicsError] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    get_analyzer().then((analyzerUrl) => {
      axios
        .get(`${analyzerUrl}/dashboard/topics`)
        .then((res) => {
          setTopics(res.data.topics || []);
          setTopicsLoading(false);
        })
        .catch((err) => {
          console.error("Failed to fetch topics:", err);
          setTopicsError("Failed to load topics.");
          setTopicsLoading(false);
        });
    });
  }, []);

  useEffect(() => {
    get_api().then((url) => {
      API_URL = url;
      console.log("API_URL:", API_URL);
    });

    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkScreenSize();
    window.addEventListener("resize", checkScreenSize);

    // Check if running as a Chrome extension
    if (
      typeof chrome !== "undefined" &&
      chrome.runtime &&
      chrome.runtime.id &&
      typeof chrome.tabs !== "undefined"
    ) {
      // Gets current url of active tab. Done by service worker
      chrome.runtime.sendMessage({ action: "getTabUrl" }, (response) => {
        if (response && response.tabUrl) {
          setArticleURL(response.tabUrl);
        }
      });

      // This will check
      const tabUrlChangeListener = () => {
        chrome.runtime.sendMessage({ action: "getTabUrl" }, (response) => {
          if (response && response.tabUrl) {
            setArticleURL(response.tabUrl);
          }
        });
      };

      // Set up a listener to check for URL change
      chrome.tabs.onActivated.addListener(tabUrlChangeListener);
      chrome.tabs.onUpdated.addListener(tabUrlChangeListener);

      return () => {
        window.removeEventListener("resize", checkScreenSize);
        chrome.tabs.onActivated.removeListener(tabUrlChangeListener);
        chrome.tabs.onUpdated.removeListener(tabUrlChangeListener);
      };
    }

    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  const handleInputChange = (event) => {
    setArticleURL(event.target.value);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmed = searchQuery.trim();
    if (trimmed) {
      navigate(`/keywords/${encodeURIComponent(trimmed)}`);
    }
  };

  const handleButtonClick = () => {
    setError(false);
    setNonNewsError(false);
    setYoutubeError(false); // ← ADD

    if (!articleURL) { setError(true); return; }
    if (isNonNewsDomain(articleURL)) { setNonNewsError(true); return; }

    new_query();
  };

  const new_query = async () => {
    try {
      if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id) {
        chrome.runtime.sendMessage({ action: "analysisStarted" });
      }
      let res = await axios.post(`${API_URL}/application/new_query`, {
        url: articleURL,
        force: forceReanalyze,
      });
      let data = res.data;
      navigate(`/results/${data.id}?redirect=false`, { state: { articleUrl: articleURL } });
    } catch (error) {
      console.error("API fetch failed:", error);

      // ── YouTube-specific error ──────────────────────────────────────────
      if (isYouTubeUrl(articleURL)) {
        setYoutubeError(true);
      } else {
        setError(true);
      }
      // ───────────────────────────────────────────────────────────────────

      if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id) {
        chrome.runtime.sendMessage({ action: "clearBadge" });
      }
    }
  };

  return (
    <div className="w-full mt-6 sm:mt-12 mb-12 flex flex-col items-center px-4 sm:px-0">
      {/* Header Text */}
      <div className="text-center mx-4 sm:mx-12 mt-8 sm:mt-16 sm:mb-8 slide-in-right">
        <h1 className="checkmate-gradient pb-4 sm:pb-8 text-3xl sm:text-5xl">
          Your Move Against Misinformation
        </h1>
        <h2 className="text-lg sm:text-2xl">
          Analyse any news article, news website video, or YouTube news video for 
          emotions, sentiment, facts, propaganda, and political bias.
        </h2>
      </div>

      {/* Search Input */}
      <div className="flex justify-center items-center w-full mt-6 sm:mt-0">
        <div className="w-[90%] sm:w-[70%] md:w-[50%]">
          <CustomInput
            placeholder="Drop an article link"
            value={articleURL}
            onChange={handleInputChange}
          />
          <p className="text-s text-slate-400 text-center mt-2">
            Supports news articles, video pages (CNN, NBC News, Today.com, Fox News…), and YouTube 
            channels from CNA, BBC, Reuters, and more
          </p>
          <br />
          <div className="flex justify-center items-center w-full mt-4 mb-8 sm:mb-16">
            <Button onClick={handleButtonClick} className="bg-blue-700">
              Analyse Now
            </Button>
          </div>
          {youtubeError && (
            <Alert variant="destructive" className="mt-2">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Unsupported YouTube Channel</AlertTitle>
              <AlertDescription>
                Only YouTube videos from news channels are supported (e.g. CNA, 
                BBC News, Reuters, NBC News). Please submit a video from a 
                recognised news organisation.
              </AlertDescription>
            </Alert>
          )}

          {nonNewsError && (
            <Alert variant="destructive" className="mt-2">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Not a News Article</AlertTitle>
              <AlertDescription>
                This URL doesn't appear to be a news source. CheckMate supports
                news articles, news outlet video pages, and YouTube videos from
                news channels (e.g. CNA, BBC, Reuters).
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Something went wrong. Please try again. Ensure that the input
                is not empty or that you are using a valid URL.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      {/* Feature Cards — grid on mobile, resizable panels on desktop */}
      <div className="flex w-full justify-center items-center slide-in-left mb-12 sm:mb-24">
        {isMobile ? (
          <div className="w-[90%] grid grid-cols-2 gap-3">
            {[
              { icon: <BadgeCheck size={24} />, title: "Fact-Checking", desc: "Make sure the content is accurate and trustworthy." },
              { icon: <Gauge size={24} />, title: "Sentiment Analysis", desc: "Find out if the article's sentiment is positive, negative, or neutral." },
              { icon: <SmilePlus size={24} />, title: "Emotion Analysis", desc: "Understand underlying emotions and see if they run high in this article." },
              { icon: <Scale size={24} />, title: "Propaganda Analysis", desc: "Check if the article leans or favours a certain side." },
              { icon: <Landmark size={24} />, title: "Political Bias", desc: "Analyze the political bias of the article and see what topics are covered or omitted." },
            ].map((item, i) => (
              <div key={i} className={`p-4 rounded-lg border bg-white ${i === 4 ? "col-span-2" : ""}`}>
                <div className="pb-2">{item.icon}</div>
                <h3 className="font-semibold pb-1 text-sm">{item.title}</h3>
                <p className="text-slate-600 text-xs">{item.desc}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="w-[75%]">
            <ResizablePanelGroup direction="horizontal" className="mb-6">
              <ResizablePanel className="m-4">
                <div className="pb-3">
                  <BadgeCheck size={30} />
                </div>
                <h3 className="font-semibold pb-3">Fact-Checking</h3>
                <p className="text-slate-600">
                  Make sure the content is accurate and trustworthy.
                </p>
              </ResizablePanel>

              <ResizableHandle />

              <ResizablePanel className="m-4">
                <div className="pb-3">
                  <Gauge size={30} />
                </div>
                <h3 className="font-semibold pb-3">Sentiment Analysis</h3>
                <p className="text-slate-600">
                  Find out if the article's sentiment is positive, negative, or
                  neutral.
                </p>
              </ResizablePanel>

              <ResizableHandle />

              <ResizablePanel className="m-4">
                <div className="pb-3">
                  <SmilePlus size={30} />
                </div>
                <h3 className="font-semibold pb-3">Emotion Analysis</h3>
                <p className="text-slate-600">
                  Understand underlying emotions and see if they run high in this
                  article.
                </p>
              </ResizablePanel>

              <ResizableHandle />

              <ResizablePanel className="m-4">
                <div className="pb-3">
                  <Scale size={30} />
                </div>
                <h3 className="font-semibold pb-3">Propaganda Analysis</h3>
                <p className="text-slate-600">
                  Check if the article leans or favours a certain side.
                </p>
              </ResizablePanel>

              <ResizableHandle />

              <ResizablePanel className="m-4">
                <div className="pb-3">
                  <Landmark size={30} />
                </div>
                <h3 className="font-semibold pb-3">Political Bias</h3>
                <p className="text-slate-600">
                  Analyze the political bias of the article and see what topics are covered or omitted.
                </p>
              </ResizablePanel>
            </ResizablePanelGroup>
          </div>
        )}
      </div>

      <div className="mx-4 sm:ml-12 sm:mr-12 w-[calc(100%-2rem)] sm:w-auto">

        {/* Guide to Political Bias Labels */}
        <BiasLabelGuide />

        {/* Latest Topics Card */}
        <div className="mb-12">
          <Card className="w-full h-[600px] sm:h-[1000px] flex flex-col">
            <CardHeader className="px-4 sm:px-6">
              <div className="flex flex-col gap-4">
                {/* Header Row: Title & Search */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <CardTitle className="text-left checkmate-gradient text-lg sm:text-2xl">
                    News Clusters — Find all the Latest News here!
                  </CardTitle>
                  
                  {/* Search Bar */}
                  <form onSubmit={handleSearchSubmit} className="flex-shrink-0">
                    <div className="relative">
                      <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                      <Input
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search articles..."
                        className="h-9 pl-8 w-48 sm:w-52 pr-3 text-sm"
                        enterKeyHint="search"
                      />
                    </div>
                  </form>
                </div>
                
                {/* Filter pills */}
                {(() => {
                  const cats = [...new Set(topics.map(t => t.topicName).filter(Boolean))].sort();
                  if (cats.length === 0) return null;
                  return (
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => setSelectedTopic(null)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${selectedTopic === null
                          ? "bg-blue-600 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                          }`}
                      >
                        All
                      </button>
                      {cats.map((cat) => (
                        <button
                          key={cat}
                          onClick={() => setSelectedTopic(selectedTopic === cat ? null : cat)}
                          className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${selectedTopic === cat
                            ? "bg-blue-600 text-white"
                            : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                            }`}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  );
                })()}
              </div>
            </CardHeader>
            <CardContent className="p-4 sm:p-6 flex-1 overflow-y-auto">
              <TopicFeed
                compact={true}
                topics={topics}
                loading={topicsLoading}
                error={topicsError}
                selectedTopic={selectedTopic}
                searchQuery={searchQuery}
              />
            </CardContent>
          </Card>
        </div>

        {/* Visualisations */}
        <div className="grid grid-cols-1 gap-8 mb-12">

          {/* Outlet Bias */}
          <Card className="flex flex-col">
            <CardHeader className="flex-none">
              <CardTitle className="checkmate-gradient text-lg sm:text-2xl">
                News Outlets: Political Bias Distribution
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 bg-transparent flex flex-col">
              <TopicOutletBias />
            </CardContent>
            <CardFooter className="px-4 sm:px-8 pt-3 from-gray-50 to-blue-50 flex items-center flex-none">
              <p className="pt-4 text-xs sm:text-base font-semibold italic">
                Ratings reflect outlet perspective only, not accuracy or credibility.
                <br />
                As such, we strongly encourage you to read outlets across the political spectrum to gain multiple perspectives.
              </p>
            </CardFooter>
          </Card>
        </div>

        {/* Trending Keywords */}
        <div>
          <Card className="w-full min-h-[200px] sm:min-h-[300px]">
            <CardContent className="p-0">
              <TrendingKeywords />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
