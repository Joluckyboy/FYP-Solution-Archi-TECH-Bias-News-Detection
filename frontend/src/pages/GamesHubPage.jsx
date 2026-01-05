import { useEffect, useState } from "react";
import { useLocation, useParams, useNavigate } from "react-router-dom";
import createSSEConnection from "@/hooks/use-SSE";
import get_api from "@/config/config";

import { HashLoader } from "react-spinners";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	CardFooter,
} from "@/components/ui/card";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
	Brain,
	Zap,
	Target,
	Eye,
	Activity,
	Pizza,
	Laugh,
	TextSearch,
	Speech,
} from "lucide-react";

import "../index.css";
// import defaultdata from "./quizoutput.json";

let API_URL = null;

// console.log("defaultdata: ", defaultdata);

const GamesPage = () => {
	const [isMobile, setIsMobile] = useState(false);
	const [activeGame, setActiveGame] = useState("bias");

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

	const navigate = useNavigate();
	const gameData = [
		{
			id: "bias",
			title: "Spot the Bias",
			icon: <Eye className="h-5 w-5" />,
			description: "Spot sneaky spin and slanted stories!",
			difficulty: "Medium",
			timeToComplete: "3 min",
			color: "bg-blue-100",
		},
		{
			id: "sentiment",
			title: "Vibe Check",
			icon: <Activity className="h-5 w-5" />,
			description: "Decode the hidden sentiments within news!",
			difficulty: "Easy",
			timeToComplete: "2 min",
			color: "bg-green-100",
		},
		{
			id: "emotion",
			title: "Gaslightin' Guesser",
			icon: <Zap className="h-5 w-5" />,
			description: "Hunt down the emotional hooks in stories!",
			difficulty: "Hard",
			timeToComplete: "5 min",
			color: "bg-purple-100",
		},
		{
			id: "propaganda",
			title: "Propaganda Profilin'",
			icon: <Target className="h-5 w-5" />,
			description: "Level up against persuasion tactics!",
			difficulty: "Expert",
			timeToComplete: "4 min",
			color: "bg-orange-100",
		},
	];

	return (
		<div
			className="app-container img-bg"
			style={{
				backgroundImage: `url('/game-bg1.jpg')`,
				backgroundSize: `480px 320px`,
				backgroundRepeat: `repeat`,
			}}
		>
			{/* Main Layout */}
			<div className="w-full max-w-5xl mx-auto p-4">
				{/* Brain Boosters Games Section */}
				<Card className="mb-6 slide-in-top">
					<CardHeader className="pb-0">
						<div className="flex items-center gap-2 mb-2">
							<Brain strokeWidth={1.5} className="h-8 w-8 text-blue-500" />
							<CardTitle
								className={`font-base checkmate-gradient ${
									isMobile ? "text-3xl" : "text-4xl"
								}`}
							>
								Brain Boosters
							</CardTitle>
						</div>
						<CardDescription className="text-base">
							Level up your news-savvy superpowers with these mind-bending
							games!
						</CardDescription>
					</CardHeader>

					<CardContent className="pt-6">
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
							{gameData.map((game) => (
								<Card
									key={game.id}
									className={`cursor-pointer transform transition-all duration-200 hover:scale-105 ${
										game.color
									} ${activeGame === game.id ? "ring-2 ring-blue-500" : ""}`}
									onClick={() => setActiveGame(game.id)}
								>
									<CardContent className="p-4">
										<div className="flex justify-between items-start">
											<div className="flex gap-3 items-center">
												<div className="p-2 bg-white rounded-full">
													{game.icon}
												</div>
												<div>
													<h3 className="font-bold text-lg">{game.title}</h3>
													<p className="text-sm text-gray-600">
														{game.description}
													</p>
												</div>
											</div>
											<div className="flex flex-col items-end gap-1">
												<Badge variant="outline" className="bg-white">
													{game.difficulty}
												</Badge>
												<span className="text-xs text-gray-500">
													{game.timeToComplete}
												</span>
											</div>
										</div>
									</CardContent>
								</Card>
							))}
						</div>

						<div className="p-4 rounded-lg mb-6 border shadow">
							<h3 className="font-bold mb-2">
								How to Play: {gameData.find((g) => g.id === activeGame)?.title}
							</h3>
							{activeGame === "bias" && (
								<p>
									Spot which headlines or articles contain sneaky bias! Compare
									two news pieces and identify loaded language, emotional
									manipulation, and slanted reporting. Sharpen your
									bias-detection skills!
								</p>
							)}
							{activeGame === "sentiment" && (
								<p>
									Judge the overall vibe of news snippets! Is it positive,
									negative, or neutral? Train your brain to detect subtle
									sentiment clues in seemingly straightforward reporting.
								</p>
							)}
							{activeGame === "emotion" && (
								<p>
									Identify which emotions the writer wants you to feel! Select
									all emotions triggered by carefully chosen words in news
									passages. Master emotional intelligence in media!
								</p>
							)}
							{activeGame === "propaganda" && (
								<p>
									Become a propaganda-fighting pro! Learn to identify common
									persuasion tactics like fear appeals, bandwagon effect, and
									glittering generalities used in news and advertising.
								</p>
							)}
						</div>
					</CardContent>

					<CardFooter className="flex justify-center">
						<Button
							size="lg"
							className="text-white font-bold px-8"
							onClick={() => navigate(`/games/quizzes?game=${activeGame}`)}
						>
							Play {gameData.find((g) => g.id === activeGame)?.title} Now!
						</Button>
					</CardFooter>
				</Card>

				{/* News Personality Quiz Section */}
				<Card className="mb-10 slide-in-bottom">
					<CardHeader className="pb-0">
						<div className="flex items-center gap-2 mb-2">
							<Brain strokeWidth={1.5} className="h-8 w-8 text-blue-500" />
							<CardTitle
								className={`font-base checkmate-gradient-flip ${
									isMobile ? "text-3xl" : "text-4xl"
								}`}
							>
								News Personality
							</CardTitle>
						</div>

						<CardDescription className="text-base">
							Discover what type of news consumer you are! Take our quick
							personality quiz.
						</CardDescription>
					</CardHeader>

					<CardContent className="pt-4">
						<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
							<div className="p-3 bg-red-100 rounded-lg flex flex-col items-center justify-center min-h-full">
								<div className="flex flex-col items-center text-center">
									<div className="px-2 w-10 mx-auto">
										<Laugh strokeWidth={1.5}></Laugh>
									</div>
									<p className="font-bold">Meme-Master Newbie</p>
									<p className="text-xs text-gray-600">
										Quick to share, loves viral news stories
									</p>
								</div>
							</div>

							<div className="p-3 bg-yellow-100 rounded-lg flex flex-col items-center justify-center min-h-full">
								<div className="flex flex-col items-center text-center">
									<div className="px-2 w-10 mx-auto">
										<Pizza strokeWidth={1.5}></Pizza>
									</div>
									<p className="font-bold">Snack-Sized News Lover</p>
									<p className="text-xs text-gray-600">
										Prefers headlines & quick summaries
									</p>
								</div>
							</div>

							<div className="p-3 bg-blue-100 rounded-lg flex flex-col items-center justify-center min-h-full">
								<div className="flex flex-col items-center text-center">
									<div className="px-2 w-10 mx-auto">
										<TextSearch strokeWidth={1.5}></TextSearch>
									</div>
									<p className="font-bold">Detective Details</p>
									<p className="text-xs text-gray-600">
										Investigates thoroughly before sharing
									</p>
								</div>
							</div>

							<div className="p-3 bg-green-100 rounded-lg flex flex-col items-center justify-center min-h-full">
								<div className="flex flex-col items-center text-center">
									<div className="px-2 w-10 mx-auto">
										<Speech strokeWidth={1.5}></Speech>
									</div>
									<p className="font-bold">Word-of-Mouth Wanderer</p>
									<p className="text-xs text-gray-600">
										Focuses on personally relevant news
									</p>
								</div>
							</div>
						</div>

						<div className="bg-gray-50 p-4 rounded-lg">
							<h3 className="font-bold mb-2">About This Quiz</h3>
							<p className="text-sm">
								Answer 5 quick questions about how you consume news and discover
								your news personality! Understanding your news consumption style
								helps you become more aware of your media habits.
							</p>
						</div>
					</CardContent>

					<CardFooter className="flex justify-center">
						<Button
							size="lg"
							className="text-white font-bold px-8"
							onClick={() => navigate(`/games/personality-quiz`)}
						>
							Take Quiz Now!
						</Button>
					</CardFooter>
				</Card>

				{/* Informational Content */}
				<div className="bg-white p-4 mx-50 rounded-lg">
					<div className="flex items-center gap-2 mb-2">
						<Zap className="h-5 w-5 text-yellow-500" />
						<h3 className="font-bold">Why These Matter</h3>
					</div>
					<p className="text-sm">
						Playing these games doesn't just make you a news pro - it helps you
						make better decisions in real life! When you can spot manipulation
						and bias, you're less likely to be fooled by fake news or clickbait.
					</p>
				</div>
			</div>
		</div>
	);
};

export default GamesPage;
