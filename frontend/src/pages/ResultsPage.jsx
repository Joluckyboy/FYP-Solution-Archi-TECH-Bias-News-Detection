import axios from "axios";
import { useEffect, useState, useRef } from "react";
import { useLocation, useParams } from "react-router-dom";
import createSSEConnection from "@/hooks/use-SSE";
import get_api from "@/config/config";

import EmotionPieChart from "@/components/EmotionPieChart";
import PropagandaTab from "@/components/PropagandaTab";

import { HashLoader } from "react-spinners";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { Progress } from "@/components/ui/progress";

import { Separator } from "@/components/ui/separator";
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/accordion";

import {
	BadgeCheck,
	BarChart2,
	Building2,
	CalendarFold,
	Gauge,
	MessageCircle,
	User,
	HeartHandshake,
	Scale,
	SmilePlus,
	NewspaperIcon,
	ClipboardList,
	LucideArrowDownFromLine,
	GlobeLock,
} from "lucide-react";

import "../index.css";
import defaultdata from "./sampleoutput.json";
import { DropdownMenu, DropdownMenuArrow } from "@radix-ui/react-dropdown-menu";

let API_URL = null;

// console.log("defaultdata: ", defaultdata);

const ResultsPage = () => {
	const location = useLocation();
	const queryParams = new URLSearchParams(location.search);
	const redirect = queryParams.get("redirect") === "true";
	const [isMobile, setIsMobile] = useState(false);

	const { id } = useParams();

	const forwarded_data = location.state?.data;
	const [data, setData] = useState(forwarded_data  || null);
	const [API_URL, setAPI_URL] = useState(null);

	useEffect(() => {
		// Fetch API_URL once
		get_api().then((url) => {
			setAPI_URL(url);
		});

		const checkScreenSize = () => {
			setIsMobile(window.innerWidth < 768);
		};

		checkScreenSize();
		window.addEventListener("resize", checkScreenSize);
		return () => window.removeEventListener("resize", checkScreenSize);
	}, []);

	useEffect(() => {
		if (!API_URL || !id) return;

		const eventSource = createSSEConnection(API_URL, id, setData);

		return () => {
			eventSource?.close(); // Cleanup on unmount
		};
	}, [API_URL, id]);

	/* Stagger Effect for Animation */
	useEffect(() => {
		const elements = document.querySelectorAll(".staggered-slide-in");
		elements.forEach((element, index) => {
			element.style.transitionDelay = `${index * 0.2}s`;
			element.classList.add("slide-in-top");
		});
	}, [data]);

	const factuality_mapping = {
		factual: "bg-teal-100 text-teal-900",
		"cannot be determined": "bg-amber-100 text-amber-900",
		unfactual: "bg-rose-100 text-rose-900",
	};

	return data ? (
		<div className="app-container">
			{/* Article Details */}
			<Card className="mb-6 staggered-slide-in">
				<CardHeader>
					<CardTitle className="text-3xl font-bold">
						{data?.title ?? "No title available"}
					</CardTitle>
					{/* Article Addtional Details */}
					<div className="flex items-center space-x-2 mt-2 card-subtitle"> 
						<GlobeLock className="w-4 h-4" />
						<a
							href={data.url}
							target="_blank"
							rel="noopener noreferrer"
							className="text-blue-500 underline"
						>
							{new URL(data.url).hostname.replace("www.", "")}
						</a>

					</div>
					{/* <div className="flex items-center space-x-2 mt-2 card-subtitle">
						<Separator orientation="vertical" className="h-4" />
						<div className="flex items-center space-x-2">
							<Building2 className="w-4 h-4" />
							<span>The Straits Times</span>
						</div>
						<Separator orientation="vertical" className="h-4" />
						<div className="flex items-center space-x-2">
							<CalendarFold className="w-4 h-4" />
							<span>22 Jan 2025</span>
						</div>
					</div> */}
				</CardHeader>
			</Card>

			{/* Main Layout */}
			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				{/* Left Column: Full Article */}
				<Card className="col-span-1 md:col-span-1 h-[70vh] staggered-slide-in">
					<CardHeader>
						<div className="flex items-center space-x-2">
							<NewspaperIcon
								strokeWidth={1.5}
								className="h-8 w-8"
							></NewspaperIcon>
							<CardTitle className="text-2xl font-base">Full Article</CardTitle>
						</div>
					</CardHeader>

					<ScrollArea className="h-[60vh]">
						<CardContent className="prose max-w-none">
							<p>{data?.content ?? "No content available"}</p>
						</CardContent>
					</ScrollArea>
				</Card>

				{/* Right Column: Summary and Analysis */}
				<div className="col-span-1 md:col-span-2 space-y-6 ">
					{/* Summary Card */}
					<Card className="staggered-slide-in">
						<CardHeader>
							<div className="flex items-center space-x-2 ">
								<ClipboardList
									strokeWidth={1.5}
									className="h-8 w-8"
								></ClipboardList>
								<CardTitle className="text-2xl font-base">
									Article Summary
								</CardTitle>
							</div>
						</CardHeader>

						<CardContent>
							<ul className="list-disc ml-6 space-y-2">
								{(data?.summarise_result ?? "No summary available")
									.split("\n\n")
									.map((paragraph, index) => (
										<li key={index}>{paragraph}</li>
									))}
							</ul>
						</CardContent>
					</Card>

					{/* Analysis Tabs */}
					<Tabs defaultValue="facts" className="w-full slide-in-right">
						<TabsList className="grid w-full grid-cols-4 gap-2 shadow">
							<TabsTrigger value="facts">Facts</TabsTrigger>
							<TabsTrigger value="sentiment">Sentiment</TabsTrigger>
							<TabsTrigger value="emotion">Emotion</TabsTrigger>
							<TabsTrigger value="propaganda">Propaganda</TabsTrigger>
						</TabsList>

						{/* Fact check */}
						<TabsContent value="facts">
							<Card className="p-4">
								<CardHeader>
									<div className="flex items-center space-x-2">
										<BadgeCheck className="h-10 w-10" />
										<CardTitle className="text-3xl">Fact-Checking</CardTitle>
									</div>
									<CardDescription>
										Make sure the content is accurate and trustworthy.
									</CardDescription>
									
									{/* Legend Segment */}
									<div className="mb-4 rounded-md border p-3 bg-white">
										<p className="mb-2">Legend:</p>
										<div className="flex flex-col space-y-2">
											<div className="flex items-center">
												<div
													className={`w-4 h-4 rounded mr-2 ${factuality_mapping["factual"]}`}
												></div>
												<span className="text-sm">
													<b>Factual</b> - Verified with reliable sources
												</span>
											</div>
											<div className="flex items-center">
												<div
													className={`w-4 h-4 rounded mr-2 ${factuality_mapping["cannot be determined"]}`}
												></div>
												<span className="text-sm">
													<b>Cannot be determined</b> - Insufficient evidence
												</span>
											</div>
											<div className="flex items-center">
												<div
													className={`w-4 h-4 rounded mr-2 ${factuality_mapping["unfactual"]}`}
												></div>
												<span className="text-sm">
													<b>Unfactual</b> - Contradicts reliable evidence
												</span>
											</div>
										</div>
									</div>
								</CardHeader>

								<Separator className="mb-4" />
								{!Array.isArray(data.factcheck_result) || data.factcheck_result.length === 0 ? (
									<CardContent>
										<div className="text-center flex flex-col items-center">
											<br />
											Analysis in progress
											<br />
											<br />
											Might take a while depending on the article length 
											<br />
											<br />
											<HashLoader color="#1E5EDD" loading={true} size={50} />
										</div>
									</CardContent>
								) : (
									<div>
										<CardContent>
											{/* Fact Check Content */}
											<div className="space-y-4">
												{data.factcheck_result.map((fact, index) => (
													<div
														key={index}
														className="flex items-center space-x-2"
													>
														<Accordion type="single" collapsible>
															<AccordionItem value={`item-${index}`}>
																<AccordionTrigger
																	className={`p-3 rounded-md ${
																		factuality_mapping[fact.correctness]
																	}`}
																>
																	<div className="flex items-start">
																		<span className="mr-2 font-semibold">
																			{index + 1}.
																		</span>
																		<span className="text-left">
																			{fact.statement}
																		</span>
																	</div>
																</AccordionTrigger>
																<AccordionContent>
																	<div className="p-4">
																		<blockquote className="border-l-2 px-4 py-2 italic text-left">
																			<span className="">
																				{fact.explanation}
																			</span>
																		</blockquote>
																		<br />
																		<p>Sources:</p>
																		<ul className="list-disc ml-6 space-y-2 text-gray-700">
																			{fact.citations.map((citation, idx) => (
																				<li key={idx}>
																					<a
																						href={citation}
																						target="_blank"
																						rel="noopener noreferrer"
																					>
																						{citation}
																					</a>
																				</li>
																			))}
																		</ul>
																	</div>
																</AccordionContent>
															</AccordionItem>
														</Accordion>
													</div>
												))}
											</div>
										</CardContent>
									</div>
								)}
							</Card>
						</TabsContent>

						{/* Sentiment Analysis */}
						<TabsContent value="sentiment">
							<Card className="p-4">
								<CardHeader>
									<div className="flex items-center space-x-2">
										<Gauge className="h-10 w-10" />
										<CardTitle className="text-3xl">
											Sentiment Analysis
										</CardTitle>
									</div>
									<CardDescription>
										Find out if the article's sentiment is positive, negative,
										or neutral.
										<br />
										<br />
										<div className="flex items-center text-start">
											<Accordion type="single" collapsible>
												<AccordionItem value="item-1">
													<AccordionTrigger className="bg-fuchsia-200 p-1 font-semibold">
														<div className="flex items-start">
															Summary of this analysis
														</div>
													</AccordionTrigger>
													<AccordionContent>
														<br />
														{data?.data_summary?.sentiment_summary ??
															"No sentiment summary available"}
													</AccordionContent>
												</AccordionItem>
											</Accordion>
										</div>
									</CardDescription>
								</CardHeader>

								<Separator />
								{data.sentiment_result === null ||
								data.sentiment_result === undefined ||
								Object.keys(data.sentiment_result).length === 0 ? (
									<CardContent>
										<div className="text-center flex flex-col items-center">
											<br />
											Analysis in progress
											<br />
											<br />
											<HashLoader color="#1E5EDD" loading={true} size={50} />
										</div>
									</CardContent>
								) : (
									<div>
										<CardContent className="space-y-4">
											{/* Sentiment Analysis Content */}
											{data.sentiment_result ? (
												Object.entries(data.sentiment_result).map(
													([key, value]) => (
														<div key={key} className="space-y-2 my-4">
															<div className="flex items-center justify-between">
																<span className="capitalize text-sm font-medium">
																	{key}
																</span>
																<span className="text-sm text-muted-foreground">
																	{(value * 100).toFixed(0)}%
																</span>
															</div>
															<Progress
																value={value * 100}
																indicatorClassName={
																	key === "positive"
																		? "bg-green-300"
																		: key === "neutral"
																		? "bg-amber-200"
																		: "bg-red-300"
																}
															></Progress>
														</div>
													)
												)
											) : (
												<div> No analysis available </div>
											)}
										</CardContent>
									</div>
								)}
							</Card>
						</TabsContent>

						{/* Emotion Analysis */}
						<TabsContent value="emotion">
							<Card className="p-4">
								<CardHeader>
									<div className="flex items-center space-x-2">
										<SmilePlus className="h-10 w-10" />
										<CardTitle>Emotion Analysis</CardTitle>
									</div>
									<CardDescription>
										Understand underlying emotions and see if they run high in
										this article.
										<br />
										<br />
										<div className="flex items-center text-start">
											<Accordion type="single" collapsible>
												<AccordionItem value="item-1">
													<AccordionTrigger className="bg-fuchsia-200 p-1 font-semibold">
														<div className="flex items-start">
															Summary of this analysis
														</div>
													</AccordionTrigger>
													<AccordionContent>
														<br />
														{data?.data_summary?.emotion_summary ??
															"No emotion summary available"}
													</AccordionContent>
												</AccordionItem>
											</Accordion>
										</div>
									</CardDescription>
								</CardHeader>

								<Separator />
								{data.emotion_result === null ||
								data.emotion_result === undefined ||
								Object.keys(data.emotion_result).length === 0 ? (
									<CardContent>
										<div className="text-center flex flex-col items-center">
											<br />
											Analysis in progress
											<br />
											<br />
											<HashLoader color="#1E5EDD" loading={true} size={50} />
										</div>
									</CardContent>
								) : (
									<div>
										<CardContent>
											{/* Emotion Analysis Content */}
											<div className="flex items-center justify-center">
												
												{data.emotion_result.weighted_avg ? (
													<EmotionPieChart
														weightedAvg={data.emotion_result.weighted_avg}
													/>
												) : (
													<div>No analysis available</div>
												)}
											</div>
										</CardContent>
									</div>
								)}
							</Card>
						</TabsContent>

						{/* Propaganda Analysis */}
						<TabsContent value="propaganda">
							<Card className="p-4">
								<CardHeader>
									<div className="flex items-center space-x-2">
										<Scale className="h-10 w-10" />
										<CardTitle className="text-3xl">
											Propaganda Analysis
										</CardTitle>
									</div>
									<CardDescription>
										Check if the article leans or favours a certain side.
										<br />
										<br />
										<div className="flex items-center text-start">
											<Accordion type="single" collapsible>
												<AccordionItem value="item-1">
													<AccordionTrigger className="bg-fuchsia-200 p-1 font-semibold">
														<div className="flex items-start">
															Summary of this analysis
														</div>
													</AccordionTrigger>
													<AccordionContent>
														<br />
														{data?.data_summary?.propaganda_summary ??
															"No propaganda summary available"}
													</AccordionContent>
												</AccordionItem>
											</Accordion>
										</div>
									</CardDescription>
								</CardHeader>

								<Separator />
								{data.propaganda_result === null ||
								data.propaganda_result === undefined ||
								Object.keys(data.propaganda_result).length === 0 ? (
									<CardContent>
										<div className="text-center flex flex-col items-center">
											<br />
											Analysis in progress
											<br />
											<br />
											<HashLoader color="#1E5EDD" loading={true} size={50} />
										</div>
									</CardContent>
								) : (
									<div>
										<div className="flex justify-center items-center my-4">
											<div className="flex items-center space-x-2">
												<PropagandaTab
													propScore={data.propaganda_result}
												></PropagandaTab>
											</div>
										</div>
										<CardContent>
											<div class="font-semibold text-lg">
												Techniques Detected:
											</div>
											{data?.propaganda_result?.formatted_result?.length !=
											0 ? (
												data.propaganda_result.formatted_result.map(
													(item, index) => (
														<div key={index} className="my-4">
															{/* The technique i.e Name-calling loaded language */}
															<div className="font-semibold text-md mb-2">
																{item[0]}
															</div>

															{/* The actual words that were identified */}
															<div className="border-2 p-4 rounded-lg bg-gray-50">
																<div className="text-sm text-gray-700">
																	"{item[1]}"
																</div>
															</div>
														</div>
													)
												)
											) : (
												<div>No propaganda technique identified</div>
											)}
										</CardContent>
									</div>
								)}
							</Card>
						</TabsContent>
					</Tabs>
				</div>
			</div>
		</div>
	) : (
		<div className="app-container flex items-center justify-center">
			<div className="text-center">
				<h1>Loading... </h1>
				<br></br>
				<HashLoader color="#1E5EDD" loading={true} size={50} />
			</div>
		</div>
	);
};

export default ResultsPage;
