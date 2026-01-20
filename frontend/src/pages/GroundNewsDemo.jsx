import React from 'react';
import TopicFeed from '@/components/TopicFeed';

const GroundNewsDemo = () => {
    return (
        <div className="min-h-screen bg-gray-50/50">
            <div className="p-8">
                <header className="mb-8 text-center">
                    <h1 className="text-4xl font-extrabold text-primary mb-2">Bias Analysis Demo</h1>
                    <p className="text-muted-foreground text-lg">Replicating the Ground News topic distribution visualizer</p>
                </header>
                <TopicFeed />
            </div>
        </div>
    );
};

export default GroundNewsDemo;
