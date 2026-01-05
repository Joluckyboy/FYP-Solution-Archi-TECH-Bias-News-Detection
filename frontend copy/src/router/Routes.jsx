import { Navigate } from "react-router-dom";
import { lazy } from "react";

// Pages
const LandingPage = lazy(() => import("@/pages/LandingPage"));
const ResultsPage = lazy(() => import("@/pages/ResultsPage"));
const GamesPage = lazy(() => import("@/pages/GamesHubPage"));

// Indiv Games and Quizzes Pages
/* const BrainBoostersPage = lazy(() => import("@/pages/GamesQuizzes/BrainBoostersPage")); */
const PersonalityQuizPage = lazy(() => import("@/pages/GamesQuizzes/PersonalityQuizPage"));
const GamesQuizPage = lazy(() => import("@/pages/GamesQuizzes/GamesQuizPage"));


export const PUBLIC_ROUTES = [
    { path: "/", element: <LandingPage /> },
    { path: "/results/:id?", element: <ResultsPage /> },
    { path: "/games", element: <GamesPage /> },
    { path: "/games/quizzes", element: <GamesQuizPage /> },
    { path: "/games/personality-quiz", element: <PersonalityQuizPage /> },
    { path: "/*", element: <Navigate to="/" /> },
];

