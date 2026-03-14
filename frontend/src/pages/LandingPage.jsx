import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
// import API_URL from "@/config/config";
import get_api, { get_analyzer } from "@/config/config";
import BiasLabelGuide from "@/components/BiasLabelGuide";
import TrendingKeywords from "@/components/TrendingKeywords";
import TopicOutletBias from "@/components/TopicOutletBias";
import TopicFeed from "@/components/TopicFeed";

import { CustomInput } from "@/components/ui/custom-input";
import { Button } from "@/components/ui/button";
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
  const [forceReanalyze] = useState(false);

  // ── Topics state (lifted here so filter pills can share it) ──────────────
  const [topics, setTopics] = useState([]);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [topicsError, setTopicsError] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);

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

  const handleButtonClick = () => {
    console.log(`Button was clicked: ${articleURL}`);
    if (!articleURL) {
      setError(true);
      return;
    }

    const new_query = async () => {
      try {
        // Notify background script that analysis is starting (for badge update)
        if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id) {
          chrome.runtime.sendMessage({ action: "analysisStarted" });
        }

        // "url": articleURL in body (not params)
        // let res = await axios.get(`${API_URL}/application/new_query`);
        let res = await axios.post(`${API_URL}/application/new_query`, {
          url: articleURL,
          force: forceReanalyze,
        });
        let data = res.data;

        // setData(apiData);
        console.log("landing page API fetch successful:", data);

        navigate(`/results/${data.id}?redirect=false`, { state: { articleUrl: articleURL } });
      } catch (error) {
        console.error("API fetch failed, using fallback JSON:", error);
        setError(true);
        // Clear badge on error
        if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.id) {
          chrome.runtime.sendMessage({ action: "clearBadge" });
        }
      }
    };

    // Redirect to the results page with the article URL in body (not params)
    // history.push("/results", { articleURL });
    new_query();
  };

  return (
    <div className="w-full">
      {/* Header Text */}
      <div className="text-center m-12 mt-48 slide-in-right">
        <h1
          className={`checkmate-gradient pb-4 ${isMobile ? "text-3xl" : "text-5xl"
            }`}
        >
          Your Move Against Misinformation
        </h1>
        <h2 className={`text-2xl ${isMobile ? "text-xl" : "text-2xl"}`}>
          Analyse any article for emotions, sentiment, and facts.
        </h2>
      </div>

      {/* Search Input */}
      <div className="flex justify-center items-center w-full mb-6">
        <div className="w-[50%]">
          <CustomInput
            placeholder="Drop an article link"
            value={articleURL}
            onChange={handleInputChange}
          />
          <br />
          <div className="flex justify-center items-center w-full mt-4 mb-16">
            <Button onClick={handleButtonClick} className="bg-blue-700">
              Analyse Now
            </Button>
          </div>
          {error ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Something went wrong. Please try again.
                <br />
                Ensure that the input is not empty or that you are using a valid
                URL.
              </AlertDescription>
            </Alert>
          ) : (
            <></>
          )}
        </div>
      </div>

      {/* Resizable Panels */}
      <div className="flex w-full justify-center items-center slide-in-left mb-12">
        <div className={`w-[75%] ${isMobile ? "h-[700px]" : ""}`}>
          <ResizablePanelGroup
            direction={isMobile ? "vertical" : "horizontal"}
            className="mb-6"
          >
            <ResizablePanel className={`m-4 ${isMobile ? "m-2" : "m-4"}`}>
              <div className="pb-3">
                <BadgeCheck size={30} />
              </div>
              <h3 className="font-semibold pb-3 ">Fact-Checking</h3>
              <p className="text-slate-600">
                Make sure the content is accurate and trustworthy.
              </p>
            </ResizablePanel>

            {/* Render the handle only in horizontal mode */}
            {!isMobile && <ResizableHandle />}

            <ResizablePanel className={`m-4 ${isMobile ? "m-2" : "m-4"}`}>
              <div className="pb-3">
                <Gauge size={30} />
              </div>
              <h3 className="font-semibold pb-3">Sentiment Analysis</h3>
              <p className="text-slate-600">
                Find out if the article's sentiment is positive, negative, or
                neutral.
              </p>
            </ResizablePanel>

            {!isMobile && <ResizableHandle />}

            <ResizablePanel className={`m-4 ${isMobile ? "m-2" : "m-4"}`}>
              <div className="pb-3">
                <SmilePlus size={30} />
              </div>
              <h3 className="font-semibold pb-3">Emotion Analysis</h3>
              <p className="text-slate-600">
                Understand underlying emotions and see if they run high in this
                article.
              </p>
            </ResizablePanel>

            {!isMobile && <ResizableHandle />}

            <ResizablePanel className={`m-4 ${isMobile ? "m-2" : "m-4"}`}>
              <div className="pb-3">
                <Scale size={30} />
              </div>
              <h3 className="font-semibold pb-3">Propaganda Analysis</h3>
              <p className="text-slate-600">
                Check if the article leans or favours a certain side.
              </p>
            </ResizablePanel>

            {!isMobile && <ResizableHandle />}

            <ResizablePanel className={`m-4 ${isMobile ? "m-2" : "m-4"}`}>
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
      </div>

      <div className="ml-12 mr-12">

        {/* Latest Topics Card */}
        <div className="mb-12">
          <Card className="w-full h-[600px] flex flex-col">
            <CardHeader>
              <div className="flex flex-col gap-3">
                <CardTitle className="text-left checkmate-gradient">Latest Topics</CardTitle>
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
            <CardContent className="p-6 flex-1 overflow-y-auto">
              <TopicFeed
                compact={true}
                topics={topics}
                loading={topicsLoading}
                error={topicsError}
                selectedTopic={selectedTopic}
              />
            </CardContent>
          </Card>
        </div>

        {/* Visualisations */}
        <div className="grid grid-cols-1 gap-8 mb-12">
          {/* Guide to Political Bias Labels */}
          <BiasLabelGuide />
          {/* Outlet Bias */}
          <Card className="h-[650px] flex flex-col">
            <CardHeader className="flex-none">
              <CardTitle className="checkmate-gradient">
                Bias Distribution
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 bg-transparent flex flex-col overflow-hidden">  
              <TopicOutletBias />
            </CardContent>
            <CardFooter className="h-20 px-8 pb-4 from-gray-50 to-blue-50 flex items-center flex-none"> 
              <p className="text-base text-gray-600 italic m-0">
                Ratings reflect outlet perspective only, not accuracy or credibility.
              </p>
            </CardFooter>
          </Card>
        </div>

        {/* Trending Keywords */}
        <div className="mb-12">
          <Card className="w-full min-h-[300px]">
            <CardHeader className="pb-3">
              <CardTitle className="text-left checkmate-gradient">Trending Keywords</CardTitle>
            </CardHeader>
            <CardContent className="p-4 h-[240px] overflow-hidden">
              <TrendingKeywords />
            </CardContent>
          </Card>
        </div>

        {/* Link to Explanations */}
        <div className="text-center mb-10">
          <Link to="/how-it-works" className="m-2 px-3 py-2 rounded-md hover:bg-gray-100 text-base font-medium inline-block">
            How This Works!
          </Link>
        </div>


      </div>

    </div>
  );
};

export default LandingPage;
