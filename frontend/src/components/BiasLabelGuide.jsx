import { useState } from "react";
import { ChevronLeft, ChevronRight, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";

const bucketColors = {
  left: "bg-blue-200 border-blue-300",
  "lean-left": "bg-blue-100 border-blue-200", 
  center: "bg-purple-100 border-gray-200",
  "lean-right": "bg-red-100 border-red-200",
  right: "bg-red-200 border-red-300"
};

const slides = [
  {
    id: "left",
    title: "Left",
    color: "left",
    explanation: 'Sources with a Left political bias label portray bias in ways that strongly align with liberal, progressive, or left-wing thought and/or policy agendas. A Left media bias rating does not necessarily mean the source is extreme, wrong, not credible, or unreasonable.',
    examplesIntro: "Sources with a Left media bias rating are <strong>most likely</strong> to show favour for:",
    examples: [
      "Generous government services (food stamps, Medicare, etc.)",
      "Rejection of social and economic inequality", 
      "Belief in systemic oppression requiring government action"
    ]
  },
  {
    id: "lean-left",
    title: "Lean Left",
    color: "lean-left",
    explanation: "Sources with a Lean Left political bias label portray bias in ways that moderately align with liberal, progressive, or left-wing thought and/or policy agendas. A Lean Left bias is a moderately liberal rating on the political spectrum.",
    examplesIntro: "Sources with a Lean Left rating <strong>may moderately</strong> show favour for at least some of the following:",
    examples: [
      "Generous government services (food stamps, Medicare, etc.)",
      "Rejection of social and economic inequality", 
      "Belief in systemic oppression requiring government action"
    ]
  },
  {
    id: "center",
    title: "Center",
    color: "center",
    explanation: "Sources with a Center political bias label either do not show much political bias or display a balance of articles with left and right perspectives. A Center media bias rating does not necessarily mean a source is totally unbiased, neutral, perfectly reasonable, or credible as it may still omit important perspectives.",
    examplesIntro: null,
    examples: [],
    centerNote: `While some Center outlets excel at providing balanced or unbiased journalism, important perspectives may still be omitted.`
    },
  {
    id: "lean-right",
    title: "Lean Right",
    color: "lean-right",
    explanation: "Sources with a Lean Right political bias label portray bias in ways that moderately align with conservative, traditional, libertarian, or right-wing thought and/or policy agendas. A Lean Right bias is a moderately conservative rating on the political spectrum.",
    examplesIntro: "Sources with a Lean Right rating <strong>may moderately</strong> show favour for at least some of the following:",
    examples: [
        "Freedom of speech",
        "Traditional family values",
        "Decreasing taxes"
      ]
  },
  {
    id: "right",
    title: "Right",
    color: "right",
    explanation: 'Sources with a Right political bias label portray bias in ways that strongly align with conservative, traditional, libertarian, or right-wing thought and/or policy agendas. A Right media bias rating does not necessarily mean the source is extreme, wrong, not credible, or unreasonable.',
    examplesIntro: "Sources with a Right media bias rating are most likely to show favour for:",
    examples: [
      "Freedom of speech",
      "Traditional family values",
      "Decreasing taxes"
    ]
  },
];

const BiasLabelGuide = () => {
    const [currentSlide, setCurrentSlide] = useState(0);
    const totalSlides = slides.length;
  
    const goNext = () => currentSlide < totalSlides - 1 && setCurrentSlide(currentSlide + 1);
    const goPrev = () => currentSlide > 0 && setCurrentSlide(currentSlide - 1);
    const goToSlide = (index) => setCurrentSlide(index);
  
    const showLeftChevron = currentSlide > 0;
    const showRightChevron = currentSlide < totalSlides - 1;
  
    return (
      <Card className="w-full mb-8 grid grid-rows-[auto_1fr_auto] max-h-[520px] md:max-h-none overflow-hidden">
        {/* Header */}
        <CardHeader className="pb-4 px-4 sm:px-6 row-start-1 flex-none h-[100px]">
        <CardTitle className="checkmate-gradient flex items-center gap-2 text-2xl font-bold">
            <Info className="h-5 w-5" />
            Left and Right — What do these political bias labels mean?
        </CardTitle>
        <p className="text-sm sm:text-base text-gray-600 mt-1 px-1">
            Source:{" "}
            <a 
            href="https://www.allsides.com/media-bias" 
            target="_blank" 
            rel="noopener noreferrer"
            className="font-medium hover:text-blue-600 hover:underline transition-colors"
            >
            AllSides Media Bias Ratings
            </a>
        </p>
        </CardHeader>
        
        <CardContent className="px-6 row-start-2 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100 max-h-[380px] md:max-h-none">
          <div className={`grid grid-rows-[auto_1fr_auto] h-full min-h-[380px] min-w-[450px] md:min-w-0 p-6 rounded-lg px-2 ${bucketColors[slides[currentSlide].color]}`}>
            {/* Navigation & Title */}
            <div className="flex items-center justify-between md:justify-start md:gap-4 p-2 row-start-1 h-[60px]">
                {/* Left Chevron */}
                <div className="ml-4 w-12 h-12 flex items-center justify-center flex-shrink-0">
                    {showLeftChevron ? (
                    <button
                        onClick={goPrev}
                        className="p-2 flex items-center justify-center"
                        aria-label="Previous slide"
                    >
                        <ChevronLeft className="h-6 w-6" />
                    </button>
                    ) : (
                    <div className="invisible" aria-hidden="true" />
                    )}
                </div>
                
                {/* Label */}
                <h3 className="text-lg md:text-xl font-bold text-gray-900 flex-1 min-w-[200px] text-center px-4">
                    {slides[currentSlide].title}
                </h3>
                
                {/* Right Chevron */}
                <div className="mr-4 w-12 h-12 flex items-center justify-center flex-shrink-0">
                    {showRightChevron ? (
                    <button
                        onClick={goNext}
                        className="p-2 flex items-center justify-center"
                        aria-label="Next slide"
                    >
                        <ChevronRight className="h-6 w-6" />
                    </button>
                    ) : (
                    <div className="invisible" aria-hidden="true" />
                    )}
                </div>
            </div>
  
            {/* Content */}
            <div className="flex flex-col gap-6 row-start-2 min-h-[260px] py-4 px-8">
              {/* Explanation */}
              <div className="prose prose-sm md:prose-base max-w-none mb-8 px-4 min-h-[120px]"> 
                <p className="mb-8 mx-6 text-sm md:text-base text-gray-800 leading-relaxed">
                <span 
                    dangerouslySetInnerHTML={{
                    __html: slides[currentSlide].explanation
                        .replace(
                        /liberal, progressive, or left-wing|conservative, traditional, libertarian, or right-wing/g,
                        '<span class="font-bold">$&</span>'
                        )
                    }} 
                />
                </p>
              
              {/* Examples */}
              <div className="bg-white/60 rounded-xl p-6 border-2 border-white/50 shadow-lg mx-4 min-h-[120px]">
                {slides[currentSlide].examplesIntro && slides[currentSlide].examples.length > 0 ? (
                    <>
                    <h4 className="font-medium mb-4 text-gray-800 text-base leading-relaxed text-left min-h-[24px]">
                        <span dangerouslySetInnerHTML={{
                        __html: slides[currentSlide].examplesIntro
                            .replace(/most likely/g, '<strong>most likely</strong>')
                            .replace(/may moderately/g, '<strong>may moderately</strong>')
                        }} />
                    </h4>
                    <ul className="mt-2 text-sm md:text-base space-y-1 ml-4 md:ml-8 list-disc min-h-[60px]">
                        {slides[currentSlide].examples.slice(0, 3).map((example, idx) => (
                        <li key={idx} className="text-sm md:text-base text-gray-800 leading-relaxed">
                            {example}
                        </li>
                        ))}
                    </ul>
                    </>
                ) : slides[currentSlide].id === "center" ? (
                    <p className="text-sm md:text-base text-center font-bold leading-relaxed italic min-h-[80px] flex items-center justify-center">
                    {slides[currentSlide].centerNote}
                    </p>
                ) : null}
                </div>
              </div>
            </div>
  
            {/* Progress Labels */}
            <div className="flex items-center justify-center gap-2 pb-4 row-start-3 h-[60px] px-6 min-w-[420px] md:min-w-0">
              {slides.map((slide, i) => {
                const shortLabel = slide.id === 'left' ? 'L' :
                                  slide.id === 'lean-left' ? 'LL' :
                                  slide.id === 'center' ? 'C' :
                                  slide.id === 'lean-right' ? 'LR' : 'R';
                const isActive = i === currentSlide;
                
                return (
                  <button
                    key={i}
                    onClick={() => goToSlide(i)}
                    className={`w-12 h-10 flex items-center justify-center rounded-full text-xs sm:text-sm font-bold transition-all duration-300 shadow-sm border-2 focus:outline-none focus:ring-2 focus:ring-offset-2 flex-shrink-0 ${
                      isActive 
                        ? 'text-white bg-black border-checkmate-gradient shadow-lg scale-110 focus:ring-checkmate-gradient' 
                        : 'text-gray-700 hover:scale-105 hover:text-gray-900 hover:border-gray-400 bg-white/80 hover:bg-white border-gray-300 focus:ring-gray-400'
                    } ${bucketColors[slide.color] || 'bg-gray-100 border-gray-200'}`} 
                    role="tab"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') goToSlide(i);
                    }}
                    aria-label={`Go to ${slide.title} slide`}
                    aria-selected={isActive}
                  >
                    {shortLabel}
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
  
        {/* CardFooter */}
        <CardFooter className="sm:px-8 row-start-3 flex-none h-[80px]">
        <p className="text-sm sm:text-base text-gray-600 italic leading-relaxed">
            A Center outlet may leave out valid perspectives or arguments from the left or right.
            <br/>
            As such, we strongly encourage you to read outlets across the political spectrum to gain multiple perspectives.
        </p>
        </CardFooter>
      </Card>
    
    );
  };
  
  export default BiasLabelGuide;
