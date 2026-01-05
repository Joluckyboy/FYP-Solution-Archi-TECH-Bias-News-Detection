import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import createSSEConnection from "@/hooks/use-SSE";
import get_api from "@/config/config";

import axios from "axios";

import { HashLoader } from "react-spinners";
import {
	Brain,
	ArrowLeft,
	ArrowRight,
	Award,
	Eye,
	Activity,
	Zap,
	Target,
} from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

import "../../index.css";
import quizData from "../quizquestion.json";
import { Separator } from "@radix-ui/react-context-menu";

const GamesQuizPage = () => {
	const location = useLocation();
	const queryParams = new URLSearchParams(location.search);
	const gameMode = queryParams.get("game");

	// Mobile Responsiveness
	const [isMobile, setIsMobile] = useState(false);

	// Data related

	// Set No. of questions to get to 5
	const numberOfQuestions = 5;

	const [data, setData] = useState(quizData || null);
	const [API_URL, setAPI_URL] = useState(null);

	// Quiz states
	const navigate = useNavigate();
	const [currentQuestion, setCurrentQuestion] = useState(0);
	const [questions, setQuestions] = useState(quizData || []);
	const [answers, setAnswers] = useState({});
	const [selectedOption, setSelectedOption] = useState(null);
	const [quizComplete, setQuizComplete] = useState(false);
	const [showingDebrief, setShowingDebrief] = useState(false);
	const [result, setResult] = useState(null);

	// Game type metadata
	const gameData = {
		bias: {
			title: "Spot the Bias",
			description: "Test your ability to identify biased headlines!",
			icon: <Eye className="h-8 w-8" />,
			color: "text-blue-500",
			bgColor: "bg-blue-50",
		},
		sentiment: {
			title: "Vibe Check",
			description: "Decode the hidden sentiments within news!",
			icon: <Activity className="h-8 w-8" />,
			color: "text-green-500",
			bgColor: "bg-green-50",
		},
		emotion: {
			title: "Gaslightin' Guesser",
			description: "Hunt down the emotional hooks in stories!",
			icon: <Zap className="h-8 w-8" />,
			color: "text-purple-500",
			bgColor: "bg-purple-50",
		},
		propaganda: {
			title: "Propaganda Profilin'",
			description: "Level up against persuasion tactics!",
			icon: <Target className="h-8 w-8" />,
			color: "text-orange-500",
			bgColor: "bg-orange-50",
		},
	};

	// Get current game metadata
	const currentGame = gameData[gameMode] || gameData.bias;

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
		if (!API_URL) return;

		axios
			.get(
				`${API_URL}/application/get_quiz?number=${numberOfQuestions}&question_type=${gameMode}`
			)
			.then((response) => {
				setQuestions(response.data.quiz);
				console.log("Questions: ", response.data.quiz);
			})
			.catch((error) => {
				console.error("Error fetching quiz data: ", error);
			});
	}, [API_URL]);

	const handleOptionSelect = (optionIndex) => {
		setSelectedOption(optionIndex);
	};

	const handleNext = () => {
		if (selectedOption !== null) {
			// Save answer
			setAnswers({
				...answers,
				[currentQuestion]: selectedOption,
			});

			// Show debrief after answering
			setShowingDebrief(true);
		}
	};

	const handleContinue = () => {
		// Reset selected option
		setSelectedOption(null);
		setShowingDebrief(false);

		// Move to next question or complete quiz
		if (currentQuestion < questions.length - 1) {
			setCurrentQuestion(currentQuestion + 1);
		} else {
			// Calculate results
			setQuizComplete(true);
		}
	};

	const handlePrevious = () => {
		if (currentQuestion > 0) {
			setCurrentQuestion(currentQuestion - 1);
			setSelectedOption(answers[currentQuestion - 1] || null);
			setShowingDebrief(false);
		}
	};

	const resetQuiz = () => {
		setCurrentQuestion(0);
		setAnswers({});
		setSelectedOption(null);
		setQuizComplete(false);
		setShowingDebrief(false);
		setResult(null);
	};

	// Calculate progress percentage
	const progress =
		questions.length > 0
			? (Object.keys(answers).length / questions.length) * 100
			: 0;

	// Check if current answer is correct
	const isCurrentAnswerCorrect = () => {
		if (questions[currentQuestion]?.answer && selectedOption !== null) {
			return questions[currentQuestion].answer.includes(selectedOption);
		}
		return false;
	};

	// Render Questions
	const renderQuestionText = (text) => {
		if (!text || typeof text !== "string") {
			return null; // Return nothing if text is undefined, null, or not a string
		}

		const parts = text.split("\\n"); // Split the text by literal "\n"
		const firstPart = parts[0]; // The overarching question
		const blockquoteParts = parts.slice(1); // The rest of the lines

		return (
			<>
				<p>{firstPart.trim()}</p>
				{blockquoteParts.map((line, index) => (
					<blockquote
						key={index}
						className="border-l-2 pl-4 italic text-gray-500 text-base"
					>
						{line.trim()}
					</blockquote>
				))}
			</>
		);
	};

	console.log(questions);

	return !questions || questions.length === 0 ? (
		<div className="text-center flex flex-col items-center">
			<br />
			<br />
			<HashLoader color="#1E5EDD" loading={true} size={50} />
		</div>
	) : (
		<div
			className="app-container img-bg min-h-screen flex items-center"
			style={{
				backgroundImage: `url('/game-bg1.jpg')`,
				backgroundSize: `480px 320px`,
				backgroundRepeat: `repeat`,
			}}
		>
			<Card className="w-full max-w-5xl mx-auto p-4">
				<CardHeader className="pb-0">
					<div className="flex items-center gap-2 mb-2">
						{currentGame.icon}
						<CardTitle
							className={`font-base ${isMobile ? "text-3xl" : "text-4xl"}`}
						>
							{currentGame.title}
						</CardTitle>
					</div>

					<CardDescription className="text-base">
						{currentGame.description}
					</CardDescription>
				</CardHeader>

				<CardContent className="pt-4 flex-grow">
					{!quizComplete ? (
						<>
							<div className="mb-4">
								<Progress value={progress} className="h-2" />
								<div className="flex justify-between mt-1 text-xs text-gray-500">
									<span>
										Question {currentQuestion + 1} of {questions.length}
									</span>
									<span>{Math.round(progress)}% complete</span>
								</div>
							</div>

							<div className="mb-6">
								{!showingDebrief ? (
									<>
										<h3 className="text-xl font-bold mb-6">
											{renderQuestionText(questions[currentQuestion]?.question)}
										</h3>

										<Separator className="h-[1px] bg-border"/>

										<RadioGroup
											value={
												selectedOption !== null
													? selectedOption.toString()
													: undefined
											}
											className="space-y-3"
										>
											{questions[currentQuestion]?.options.map(
												(option, index) => (
													<div
														key={index}
														className="flex items-start space-x-2 mt-4 p-2 rounded-md hover:bg-gray-50 cursor-pointer"
														onClick={() => handleOptionSelect(index)}
													>
														<RadioGroupItem
															value={index.toString()}
															id={`option-${index}`}
														/>
														<Label
															htmlFor={`option-${index}`}
															className="flex-grow cursor-pointer"
														>
															{option}
														</Label>
													</div>
												)
											)}
										</RadioGroup>
									</>
								) : (
									// Debrief after answering
									<div className="text-center">
										<div
											className={`p-5 rounded-full inline-block ${
												isCurrentAnswerCorrect()
													? "bg-green-100"
													: "bg-amber-100"
											} mb-4`}
										>
											<Award
												className={`h-12 w-12 ${
													isCurrentAnswerCorrect()
														? "text-green-700"
														: "text-amber-700"
												}`}
											/>
										</div>

										<h2 className="text-xl font-bold mb-2">
											{isCurrentAnswerCorrect()
												? "That's Correct!"
												: "Not Quite Right"}
										</h2>

										<Badge variant="secondary" className="mb-4">
											Explanation
										</Badge>

										<div
											className={`${
												isCurrentAnswerCorrect()
													? "bg-green-100"
													: "bg-amber-100"
											} p-4 rounded-lg mb-4 text-left`}
										>
											<p className="text-sm">
												{questions[currentQuestion]?.debrief}
											</p>
										</div>
									</div>
								)}
							</div>
						</>
					) : (
						// Quiz complete screen
						<div className="text-center">
							<div
								className={`p-6 rounded-full inline-block ${currentGame.bgColor} mb-4`}
							>
								<Award className={`h-16 w-16 ${currentGame.color}`} />
							</div>

							<h2 className="text-2xl font-bold mb-2">Quiz Complete!</h2>

							<Badge variant="secondary" className="mb-4">Results</Badge>

							<p className="mb-4 text-gray-700">
								You've completed the {currentGame.title} challenge!
							</p>

							<div
								className={`${currentGame.bgColor} p-4 rounded-lg mb-4 text-left`}
							>
								<h3 className="font-bold mb-1">What You've Learned:</h3>
								<p className="text-sm">
									You've practiced identifying{" "}
									{gameMode === "bias"
										? "biased language and slanted stories"
										: gameMode === "sentiment"
										? "emotional tones and hidden sentiments"
										: gameMode === "emotion"
										? "emotional manipulation techniques"
										: "propaganda and persuasion tactics"}{" "}
									in news media. Keep practicing to sharpen your critical
									thinking skills!
								</p>
							</div>
						</div>
					)}
				</CardContent>

				<CardFooter className="flex justify-between">
					{!quizComplete ? (
						<>
							{!showingDebrief ? (
								<>
									<Button
										variant="outline"
										onClick={handlePrevious}
										disabled={currentQuestion === 0}
									>
										<ArrowLeft className="mr-1 h-4 w-4" /> Previous
									</Button>

									<Button
										onClick={handleNext}
										disabled={selectedOption === null}
									>
										Submit Answer
									</Button>
								</>
							) : (
								<div className="flex justify-end align-items-center w-full">
									<Button onClick={handleContinue}>
										{currentQuestion < questions.length - 1 ? (
											<>
												Continue <ArrowRight className="ml-1 h-4 w-4 " />
											</>
										) : (
											"See Final Results"
										)}
									</Button>
								</div>
							)}
						</>
					) : (
						<div className="w-full flex gap-4">
							<Button variant="outline" className="flex-1" onClick={resetQuiz}>
								Retake Quiz
							</Button>
							<Button className="flex-1" onClick={() => navigate("/games")}>
								Back to Games
							</Button>
						</div>
					)}
				</CardFooter>
			</Card>
		</div>
	);
};

export default GamesQuizPage;
