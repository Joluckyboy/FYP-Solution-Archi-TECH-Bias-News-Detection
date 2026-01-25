import { Card, CardContent, CardFooter } from "@/components/ui/card";

const TopicCard = ({ topic }) => {
    const { title, image, sourceCount, biasDistribution } = topic;

    // Calculate total for percentages if not provided, though we expect pre-calculated percentages or counts
    const total = biasDistribution.left + biasDistribution.leaning_left + biasDistribution.center + biasDistribution.leaning_right + biasDistribution.right;
    const leftPct = ((biasDistribution.left + biasDistribution.leaning_left) / total) * 100;
    const centerPct = (biasDistribution.center / total) * 100;
    const rightPct = ((biasDistribution.right + biasDistribution.leaning_right) / total) * 100;

    return (
        <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-300 flex flex-col h-full border-none shadow-md">
            {/* Image Section */}
            <div className="relative h-48 w-full overflow-hidden">
                <img
                    src={image}
                    alt={title}
                    className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                    <h3 className="text-white font-bold text-lg leading-tight line-clamp-2 drop-shadow-md">
                        {title}
                    </h3>
                </div>
            </div>

            <CardContent className="p-4 flex-grow">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                        {sourceCount} Sources
                    </span>
                    {/* Placeholder for time or other metadata if needed */}
                </div>

                {/* Bias Bar Chart */}
                <div className="mt-2">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1 font-semibold">
                        <span className="text-blue-600">Left {Math.round(leftPct)}%</span>
                        <span className="text-gray-500">Center {Math.round(centerPct)}%</span>
                        <span className="text-red-600">Right {Math.round(rightPct)}%</span>
                    </div>

                    <div className="h-3 w-full flex rounded-full overflow-hidden bg-gray-100">
                        {/* Left Segment */}
                        <div
                            className="h-full bg-blue-500 first:rounded-l-full relative group"
                            style={{ width: `${leftPct}%` }}
                        >
                        </div>

                        {/* Center Segment */}
                        <div
                            className="h-full bg-gray-300 relative group"
                            style={{ width: `${centerPct}%` }}
                        >
                        </div>

                        {/* Right Segment */}
                        <div
                            className="h-full bg-red-500 last:rounded-r-full relative group"
                            style={{ width: `${rightPct}%` }}
                        >
                        </div>
                    </div>

                    <div className="flex justify-between text-[10px] text-gray-400 mt-1 px-1">
                        <span>Democratic</span>
                        <span>Independent</span>
                        <span>Republican</span>
                    </div>
                </div>
            </CardContent>

            <CardFooter className="p-4 pt-0">
                <button className="w-full py-2 bg-secondary/10 hover:bg-secondary/20 text-secondary-foreground text-sm font-medium rounded-md transition-colors">
                    View Full Coverage
                </button>
            </CardFooter>
        </Card>
    );
};

export default TopicCard;
