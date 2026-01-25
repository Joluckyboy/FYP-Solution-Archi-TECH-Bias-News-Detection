import { Navigate } from "react-router-dom";
import { lazy } from "react";

// Pages
const LandingPage = lazy(() => import("@/pages/LandingPage"));
const ResultsPage = lazy(() => import("@/pages/ResultsPage"));
const GamesPage = lazy(() => import("@/pages/GamesHubPage"));
const OutletBiasPage = lazy(() => import("@/pages/OutletBiasPage"));

// Indiv Games and Quizzes Pages
/* const BrainBoostersPage = lazy(() => import("@/pages/GamesQuizzes/BrainBoostersPage")); */
const PersonalityQuizPage = lazy(() => import("@/pages/GamesQuizzes/PersonalityQuizPage"));
const GamesQuizPage = lazy(() => import("@/pages/GamesQuizzes/GamesQuizPage"));
const LatestNewsPage = lazy(() => import("@/pages/LatestNewsPage"));
// Dashboard
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));

export const PUBLIC_ROUTES = [
    { path: "/", element: <LandingPage /> },
    { path: "/results/:id?", element: <ResultsPage /> },
    { path: "/games", element: <GamesPage /> },
    { path: "/games/quizzes", element: <GamesQuizPage /> },
    { path: "/games/personality-quiz", element: <PersonalityQuizPage /> },
    { path: "/outlet-bias", element: <OutletBiasPage /> },
    { path: "/latest-news-coverage", element: <LatestNewsPage /> },
    { path: "/*", element: <Navigate to="/" /> },
    { path: "/dashboard", element: <DashboardPage /> },
];

