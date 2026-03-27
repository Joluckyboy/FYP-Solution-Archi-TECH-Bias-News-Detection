import { useEffect, useState } from 'react';
import TopicCard from './TopicCard';
import axios from 'axios';
import { get_analyzer } from '@/config/config';
import { Loader2 } from 'lucide-react';

/**
 * TopicFeed can operate in two modes:
 *  1. Managed externally – pass `topics` + `loading` + `error` props (used by LandingPage
 *     so the filter pills share the same data).
 *  2. Self-contained – omit those props; the component fetches its own data (legacy / standalone).
 */
const TopicFeed = ({
    compact = false,
    topics: topicsProp = null,
    loading: loadingProp = null,
    error: errorProp = null,
    selectedTopic = null,
    searchQuery = "",
}) => {
    const [topicsInternal, setTopicsInternal] = useState([]);
    const [loadingInternal, setLoadingInternal] = useState(true);
    const [errorInternal, setErrorInternal] = useState(null);

    const isManaged = topicsProp !== null;
    const topics = isManaged ? topicsProp : topicsInternal;
    const loading = isManaged ? loadingProp : loadingInternal;
    const error = isManaged ? errorProp : errorInternal;

    useEffect(() => {
        if (isManaged) return; // parent controls data
        const fetchTopics = async () => {
            try {
                const ANALYZER_URL = await get_analyzer();
                const response = await axios.get(`${ANALYZER_URL}/dashboard/topics`);
                setTopicsInternal(response.data.topics);
                setLoadingInternal(false);
            } catch (err) {
                console.error("Failed to fetch topics:", err);
                setErrorInternal("Failed to load topics. Please ensure the backend analyzer service is running.");
                setLoadingInternal(false);
            }
        };
        fetchTopics();
    }, [isManaged]);

    let filteredTopics = selectedTopic
        ? topics.filter(t => t.topicName === selectedTopic)
        : topics;

    if (searchQuery) {
        filteredTopics = filteredTopics.filter(t => 
            (t.title || "").toLowerCase().includes(searchQuery.toLowerCase())
        );
    }

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
        <div className={compact ? "w-full" : "container mx-auto py-8"}>
            {!compact && <h2 className="text-3xl font-bold mb-6 tracking-tight">Latest Topics</h2>}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredTopics.map(topic => (
                    <TopicCard key={topic.id} topic={topic} />
                ))}
                {filteredTopics.length === 0 && (
                    <div className="col-span-3 text-center py-12 text-muted-foreground">
                        No topics found for this category.
                    </div>
                )}
            </div>
        </div>
    );
};

export default TopicFeed;
