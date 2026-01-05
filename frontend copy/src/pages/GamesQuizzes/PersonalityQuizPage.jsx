import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import createSSEConnection from "@/hooks/use-SSE";
import get_api from "@/config/config";

import axios from "axios";

import { HashLoader } from "react-spinners";
import { Brain, ArrowLeft, ArrowRight, Award } from "lucide-react";
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
import quizData from "../personalityquestion.json";
let API_URL = null;

const PersonalityQuizPage = () => {
	const location = useLocation();
	const queryParams = new URLSearchParams(location.search);

	// Mobile Responsiveness
	const [isMobile, setIsMobile] = useState(false);

	// Data related
	const [data, setData] = useState(quizData || null);
	const [API_URL, setAPI_URL] = useState(null);

	// Quiz states
	const navigate = useNavigate();
	const [currentQuestion, setCurrentQuestion] = useState(0);
	const [questions, setQuestions] = useState(quizData || [] );
	const [answers, setAnswers] = useState({});
	const [selectedOption, setSelectedOption] = useState(null);
	const [quizComplete, setQuizComplete] = useState(false);
	const [result, setResult] = useState(null);

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
			.get(`${API_URL}/application/get_quiz?number=5&question_type=personality`)
			.then((response) => {
				setQuestions(response.data.quiz);
				console.log("Questions: ", questions);
			})
			.catch((error) => {
				console.error("Error fetching quiz data: ", error);
				/* console.log("Using fallback quizData");
				setQuestions(quizData.quiz); */
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

			// Reset selected option
			setSelectedOption(null);

			// Move to next question or complete quiz
			if (currentQuestion < questions.length - 1) {
				setCurrentQuestion(currentQuestion + 1);
			} else {
				// Calculate results
				calculateResults();
			}
		}
	};

	const handlePrevious = () => {
		if (currentQuestion > 0) {
			setCurrentQuestion(currentQuestion - 1);
			setSelectedOption(answers[currentQuestion - 1] || null);
		}
	};

	const resetQuiz = () => {
		setCurrentQuestion(0);
		setAnswers({});
		setSelectedOption(null);
		setQuizComplete(false);
		setResult(null);
	};

	// Calculate progress percentage
	const progress =
		questions.length > 0
			? (Object.keys(answers).length / questions.length) * 100
			: 0;

	const calculateResults = () => {
		// Count answers by option index
		const counts = [0, 0, 0, 0]; // For each personality type

		Object.values(answers).forEach((answerIndex) => {
			counts[answerIndex]++;
		});

		// Find the dominant personality type
		const maxCount = Math.max(...counts);
		const dominantTypes = counts
			.map((count, index) => ({ index, count }))
			.filter((item) => item.count === maxCount)
			.map((item) => item.index);

		// In case of a tie, just pick the first one
		const dominantType = dominantTypes[0];

		// Set result based on dominant personality type
		const personalities = [
			{
				type: "Meme-Master Newbie",
				description:
					"You're quick to share news and love viral content. While your social media game is strong, be cautious about spreading misinformation in your enthusiasm!",
				color: "bg-red-100",
				textColor: "text-red-700",
				tips: "Take a moment to verify before sharing. Your influence is powerful!",
			},
			{
				type: "Snack-Sized News Lover",
				description:
					"You prefer headlines and quick summaries. Your efficiency helps you stay informed, but sometimes you might miss important context.",
				color: "bg-yellow-100",
				textColor: "text-yellow-700",
				tips: "Occasionally dive deeper into topics that matter most to you.",
			},
			{
				type: "Detective Details",
				description:
					"You investigate thoroughly before forming opinions. Your careful approach means you're rarely fooled, but you might sometimes miss breaking news.",
				color: "bg-blue-100",
				textColor: "text-blue-700",
				tips: "Keep up your fact-checking habits - the news world needs more people like you!",
			},
			{
				type: "Word-of-Mouth Wanderer",
				description:
					"You focus on news that directly impacts you. While this keeps you grounded, you might miss important global events.",
				color: "bg-green-100",
				textColor: "text-green-700",
				tips: "Try expanding your news horizons occasionally to broaden your perspective.",
			},
		];

		setResult(personalities[dominantType]);
		setQuizComplete(true);
	};

	return !questions ? (
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
			<Card className="w-full max-w-5xl h-full mx-auto p-4 ">
				<CardHeader className="pb-0">
					<div className="flex items-center gap-2 mb-2">
						<Brain strokeWidth={1.5} className="h-8 w-8 text-blue-500" />
						<CardTitle
							className={`font-base checkmate-gradient-flip ${
								isMobile ? "text-3xl" : "text-4xl"
							}`}
						>
							News Personality Quiz
						</CardTitle>
					</div>

					<CardDescription className="text-base">
						Discover what type of news consumer you are!
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
								<h3 className="text-xl font-bold mb-4">
									{questions[currentQuestion]?.question}
								</h3>

								<RadioGroup
									value={
										selectedOption !== null
											? selectedOption.toString()
											: undefined
									}
									className="space-y-3"
								>
									{questions[currentQuestion]?.options.map((option, index) => (
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
									))}
								</RadioGroup>
							</div>
						</>
					) : (
						<div className="text-center">
							<div
								className={`p-6 rounded-full inline-block ${result.color} mb-4`}
							>
								<Award className={`h-16 w-16 ${result.textColor}`} />
							</div>

							<h2 className="text-2xl font-bold mb-2">
								You're a {result.type}!
							</h2>

							<Badge variant="secondary" className={`${result.textColor} mb-4`}>
								{result.type}
							</Badge>

							<p className="mb-4 text-gray-700">{result.description}</p>

							<div className="bg-muted p-4 rounded-lg mb-4 text-left">
								<h3 className="font-bold mb-1">Quick Tip:</h3>
								<p className="text-sm">{result.tips}</p>
							</div>
						</div>
					)}
				</CardContent>

				<CardFooter className="flex justify-between">
					{!quizComplete ? (
						<>
							<Button
								variant="outline"
								onClick={handlePrevious}
								disabled={currentQuestion === 0}
							>
								<ArrowLeft className="mr-2 h-4 w-4" /> Previous
							</Button>

							<Button onClick={handleNext} disabled={selectedOption === null}>
								{currentQuestion < questions.length - 1 ? (
									<>
										Next <ArrowRight className="ml-2 h-4 w-4" />
									</>
								) : (
									"See Results"
								)}
							</Button>
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

export default PersonalityQuizPage;
