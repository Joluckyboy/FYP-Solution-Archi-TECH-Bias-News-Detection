import { Routes, Route, BrowserRouter, HashRouter } from "react-router-dom"
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton"

import { PUBLIC_ROUTES } from "./Routes"
import Layout from "@/components/layout/Layout";


export const AppRouter = () => {
    const renderRoutes = (routes) => {
        return routes.map((route, idx) => (
            <Route
                key={idx}
                path={route.path}
                element={route.element}
            />
        ));
    };

    return (
        <>
            <HashRouter
                future={{
                    v7_startTransition: true,
                    v7_relativeSplatPath: true,
                }}
            >
                <Suspense fallback={<Skeleton />}>
                    <Routes>
                        <Route element={<Layout />}>
                            {renderRoutes(PUBLIC_ROUTES)}
                        </Route>
                    </Routes>
                </Suspense>
            </HashRouter>
        </>
    );
};