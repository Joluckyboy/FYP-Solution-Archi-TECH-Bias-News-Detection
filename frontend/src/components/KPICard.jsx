import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

/**
 * KPICard Component
 * Displays a key performance indicator with an icon, title, and value.
 * 
 * @param {Object} props
 * @param {string} props.title - Title of the KPI
 * @param {string|number} props.value - Value to display
 * @param {React.ReactNode} props.icon - Icon component
 * @param {string} props.description - Optional description
 * @param {boolean} props.loading - Loading state
 */
const KPICard = ({ title, value, icon, description, loading = false }) => {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                    {title}
                </CardTitle>
                {icon && <div className="h-4 w-4 text-muted-foreground">{icon}</div>}
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Loading...</span>
                    </div>
                ) : (
                    <>
                        <div className="text-2xl font-bold">{value}</div>
                        {description && (
                            <p className="text-xs text-muted-foreground">
                                {description}
                            </p>
                        )}
                    </>
                )}
            </CardContent>
        </Card>
    );
};

export default KPICard;
