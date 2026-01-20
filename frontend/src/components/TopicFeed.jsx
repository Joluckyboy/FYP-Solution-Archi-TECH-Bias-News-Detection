import React, { useEffect, useState } from 'react';
import TopicCard from './TopicCard';
import axios from 'axios';
import { Loader2 } from 'lucide-react';

const TopicFeed = () => {
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchTopics = async () => {
            try {
                // Assuming the scraper service runs on localhost:5000
                const response = await axios.get('http://127.0.0.1:8015/scraper/dashboard/topics');
                setTopics(response.data.topics);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch topics:", err);
                setError("Failed to load topics. Please ensure the backend scraper service is running.");
                setLoading(false);
            }
        };

        fetchTopics();
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center py-20">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center py-20 text-red-500">
                <p>{error}</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8">
            <h2 className="text-3xl font-bold mb-6 tracking-tight">Latest Topics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {topics.map(topic => (
                    <TopicCard key={topic.id} topic={topic} />
                ))}
            </div>
        </div>
    );
};

export default TopicFeed;
