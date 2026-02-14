import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
// import API_URL from "@/config/config";
import get_api from "@/config/config";
import TrendingKeywords from "../components/TrendingKeywords";
import OutletBiasChart from "../components/OutletBiasChart";
import TopicOutletDistribution from "../components/TopicOutletDistribution";
import TopicFeed from "@/components/TopicFeed";

import { CustomInput } from "@/components/ui/custom-input";
import { Button } from "@/components/ui/button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { BadgeCheck, Scale, AlertCircle, Gauge, SmilePlus } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

import axios from "axios";

let API_URL = null;

const LandingPage = () => {
  let navigate = useNavigate();
  const [articleURL, setArticleURL] = useState("");
  const [isMobile, setIsMobile] = useState(false);
  const [error, setError] = useState(false);
  const [forceReanalyze] = useState(false);

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
      <div className="text-center m-12 slide-in-right">
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
          <div className="flex justify-center items-center w-full mb-16">
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
          </ResizablePanelGroup>
        </div>
      </div>

      <div className="ml-12 mr-12">

        {/* Topics Divider */}
        <div className="w-full h-px bg-black border-0 mb-12"></div>

        {/* Latest Topics Card */}
        <div className="mb-12">
          <Card className="w-full h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle className="text-left checkmate-gradient">Latest Topics</CardTitle>
            </CardHeader>
            <CardContent className="p-6 flex-1 overflow-y-auto">
              <TopicFeed compact={true} />
            </CardContent>
          </Card>
        </div>

        {/* Trending Keywords Card */}
        <div className="mb-12">
          <Card className="w-full h-[400px]">
            <CardHeader>
              <CardTitle className="text-left checkmate-gradient">Trending Keywords</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <TrendingKeywords />
            </CardContent>
          </Card>
        </div>

        {/* Visualisations */}
        <div className="grid grid-cols-2 gap-8 mb-12">
          {/* Articles per Outlet, filterable by topic */}
          <Card className="h-[500px]">
            <CardHeader>
              <CardTitle className="text-left checkmate-gradient">Topic Coverage</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <TopicOutletDistribution />
            </CardContent>
          </Card>

          {/* Outlet Bias */}
          <Card className="h-[500px]">
            <CardHeader>
              <CardTitle className="checkmate-gradient">
                Outlet Bias Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <OutletBiasChart />
              <p className="text-sm">Ratings do not reflect accuracy or credibility, they reflect perspective only.</p>
            </CardContent>
          </Card>
        </div>

        {/* Final Divider */}
        <div className="w-full h-px bg-black border-0 mb-8"></div>

        {/* Link to Explanations */}
        <div className="text-center">
          <p className="text-xl checkmate-gradient">More About:</p>
          <Link to="/how-it-works" className="m-2 px-3 py-2 rounded-md hover:bg-gray-100 text-base font-medium inline-block">
            How This Works!
          </Link>
        </div>

      </div>

    </div>
  );
};

export default LandingPage;
