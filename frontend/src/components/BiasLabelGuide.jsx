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
      <Card className="w-full max-w-none mb-8">
        {/* Header */}
        <CardHeader className="pb-4">
        <CardTitle className="checkmate-gradient flex items-center gap-2 text-2xl font-bold">
            <Info className="h-5 w-5" />
            Left and Right — What do these political bias labels mean?
        </CardTitle>
        <p className="text-base text-gray-600 mt-1">
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
        
        <CardContent className="p-0 pb-8">
          <div className={`p-8 rounded-lg ${bucketColors[slides[currentSlide].color]} h-full`}>
            {/* Navigation & Title */}
            <div className="flex items-center gap-4 mb-8 h-14">
                {/* Left Chevron */}
                <div className="w-12 h-12 flex items-center justify-center">
                    {showLeftChevron ? (
                    <button
                        onClick={goPrev}
                        className="p-2 rounded-full hover:bg-white/50"
                        aria-label="Previous slide"
                    >
                        <ChevronLeft className="h-6 w-6" />
                    </button>
                    ) : (
                    <div className="w-10 h-10 rounded-full invisible" aria-hidden="true" />
                    )}
                </div>
                
                {/* Label */}
                <h3 className="text-base font-bold text-gray-900">
                    {slides[currentSlide].title}
                </h3>
                
                {/* Right Chevron */}
                <div className="w-12 h-12 flex items-center justify-center">
                    {showRightChevron ? (
                    <button
                        onClick={goNext}
                        className="p-2 rounded-full hover:bg-white/50"
                        aria-label="Next slide"
                    >
                        <ChevronRight className="h-6 w-6" />
                    </button>
                    ) : (
                    <div className="w-10 h-10 rounded-full invisible" aria-hidden="true" />
                    )}
                </div>
            </div>
  
            {/* Content */}
            <div className="prose prose-base max-w-none mb-12"> 
            <p className="mb-8 text-gray-800 leading-relaxed text-base px-4">
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
              <div className="bg-white/60 rounded-xl p-8 border-2 border-white/50 shadow-lg">
                {slides[currentSlide].examplesIntro && slides[currentSlide].examples.length > 0 ? (
                    <>
                    <h4 className="font-medium mb-4 text-gray-800 text-base leading-relaxed text-left">
                        <span dangerouslySetInnerHTML={{
                        __html: slides[currentSlide].examplesIntro
                            .replace(/most likely/g, '<strong>most likely</strong>')
                            .replace(/may moderately/g, '<strong>may moderately</strong>')
                        }} />
                    </h4>
                    <ul className="mt-2 text-base space-y-1 ml-8 list-disc">
                        {slides[currentSlide].examples.slice(0, 3).map((example, idx) => (
                        <li key={idx} className="text-base text-gray-800 leading-relaxed ml-4">
                            {example}
                        </li>
                        ))}
                    </ul>
                    </>
                ) : slides[currentSlide].id === "center" ? (
                    <p className="text-base text-center font-bold leading-relaxed italic">
                    {slides[currentSlide].centerNote}
                    </p>
                ) : null}
                </div>
            </div>
  
            {/* Progress Lines */}
            <div className="flex items-center justify-center gap-3 pb-4"> 
              {Array.from({ length: totalSlides }, (_, i) => (
                <div
                  key={i}
                  onClick={() => goToSlide(i)}
                  className={`w-12 h-1.5 rounded-full cursor-pointer transition-all duration-300 hover:scale-[1.15] shadow-sm ${
                    i === currentSlide 
                      ? "bg-gray-900"  
                      : "bg-gray-300 hover:bg-gray-400"  
                  }`}
                  aria-label={`Go to slide ${i + 1}`}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      goToSlide(i);
                    }
                  }}
                />
              ))}
            </div>
          </div>
        </CardContent>
  
        {/* CardFooter */}
        <CardFooter className="pb-6 px-8">
        <p className="text-base text-gray-600 italic leading-relaxed"> {/* text-base */}
            A Center outlet may leave out valid perspectives or arguments from the left or right. <br/>
            As such, we strongly encourage you to read outlets across the political spectrum to gain multiple perspectives.
        </p>
        </CardFooter>
      </Card>
    );
  };
  
  export default BiasLabelGuide;
