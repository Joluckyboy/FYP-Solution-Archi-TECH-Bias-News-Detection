import { Navigate } from "react-router-dom";
import { lazy } from "react";

// Pages
const LandingPage = lazy(() => import("@/pages/LandingPage"));
const ResultsPage = lazy(() => import("@/pages/ResultsPage"));
const PopupPage = lazy(() => import("@/pages/PopupPage"));
const GamesPage = lazy(() => import("@/pages/GamesHubPage"));

// Indiv Games and Quizzes Pages
/* const BrainBoostersPage = lazy(() => import("@/pages/GamesQuizzes/BrainBoostersPage")); */
const PersonalityQuizPage = lazy(() => import("@/pages/GamesQuizzes/PersonalityQuizPage"));
const GamesQuizPage = lazy(() => import("@/pages/GamesQuizzes/GamesQuizPage"));
const FullCoveragePage = lazy(() => import("@/pages/FullCoveragePage"));
// Dashboard
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
// How It Works
const HowItWorksPage = lazy(() => import("@/pages/HowItWorksPage"));

export const PUBLIC_ROUTES = [
    { path: "/", element: <LandingPage /> },
    { path: "/results/:id?", element: <ResultsPage /> },
    { path: "/games", element: <GamesPage /> },
    { path: "/games/quizzes", element: <GamesQuizPage /> },
    { path: "/games/personality-quiz", element: <PersonalityQuizPage /> },
    { path: "/full-coverage/:topicId", element: <FullCoveragePage /> },
    { path: "/*", element: <Navigate to="/" /> },
    { path: "/dashboard", element: <DashboardPage /> },
    { path: "/how-it-works", element: <HowItWorksPage /> },
    { path: "/*", element: <Navigate to="/" /> },
];

// Popup route (no layout)
export const POPUP_ROUTE = { path: "/popup", element: <PopupPage /> };

