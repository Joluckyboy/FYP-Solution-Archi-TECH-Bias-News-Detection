import { useState } from "react";
import { ChevronLeft, ChevronRight, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";

const bucketColors = {
  left: "bg-blue-200",
  "lean-left": "bg-blue-100",
  center: "bg-purple-100",
  "lean-right": "bg-red-100",
  right: "bg-red-200"
};

const progressBarColors = {
  left: "bg-blue-200",
  "lean-left": "bg-blue-100",
  center: "bg-purple-200",
  "lean-right": "bg-red-100",
  right: "bg-red-200"
};

const slides = [
  {
    id: "left",
    title: "Left",
    color: "left",
    explanation: 'Sources with a Left political bias label portray bias in ways that strongly align with liberal, progressive, or left-wing thought and/or policy agendas. A Left media bias rating does not necessarily mean the source is extreme, wrong, not credible, or unreasonable.',
    examplesIntro: "Sources with a Left media bias rating are <strong>most likely</strong> to show favour for:",
    examples: [
      "Generous government services (GST vouchers, healthcare support, etc.)",
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
      "Generous government services (GST vouchers, healthcare support, etc.)",
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
    <Card className="w-full mb-8">

      {/* Header */}
      <CardHeader className="pb-4 px-4 sm:px-6">
        <CardTitle className="checkmate-gradient flex items-center gap-2 text-xl sm:text-2xl leading-snug">
          <Info className="h-5 w-5 flex-shrink-0" />
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

      <CardContent className="px-4 sm:px-6">
        <div className={`flex flex-col rounded-lg p-4 sm:p-6 ${bucketColors[slides[currentSlide].color]}`}>

          {/* Navigation & Title */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="w-10 h-10 flex items-center justify-center flex-shrink-0">
              {showLeftChevron ? (
                <button onClick={goPrev} className="p-2 flex items-center justify-center" aria-label="Previous slide">
                  <ChevronLeft className="h-6 w-6" />
                </button>
              ) : (
                <div className="invisible" aria-hidden="true" />
              )}
            </div>

            <h3 className="text-lg sm:text-xl font-bold text-gray-900 text-center flex-1">
              {slides[currentSlide].title}
            </h3>

            <div className="w-10 h-10 flex items-center justify-center flex-shrink-0">
              {showRightChevron ? (
                <button onClick={goNext} className="p-2 flex items-center justify-center" aria-label="Next slide">
                  <ChevronRight className="h-6 w-6" />
                </button>
              ) : (
                <div className="invisible" aria-hidden="true" />
              )}
            </div>
          </div>

          {/* Content */}
          <div className="flex flex-col gap-4 px-2 sm:px-6 mb-5">

            {/* Explanation box */}
            <div className="bg-white/60 rounded-xl p-4 sm:p-6 border-2 border-white/50 shadow-lg">
              <p
                className="text-sm sm:text-base text-gray-800 leading-relaxed"
                dangerouslySetInnerHTML={{
                  __html: slides[currentSlide].explanation.replace(
                    /liberal, progressive, or left-wing|conservative, traditional, libertarian, or right-wing/g,
                    '<span class="font-bold">$&</span>'
                  )
                }}
              />
            </div>

            {/* Examples */}
            {slides[currentSlide].examplesIntro && slides[currentSlide].examples.length > 0 ? (
              <div className="px-2">
                <h4 className="font-medium mb-3 text-gray-800 text-sm sm:text-base leading-relaxed">
                  <span dangerouslySetInnerHTML={{
                    __html: slides[currentSlide].examplesIntro
                      .replace(/most likely/g, '<strong>most likely</strong>')
                      .replace(/may moderately/g, '<strong>may moderately</strong>')
                  }} />
                </h4>
                <ul className="text-sm sm:text-base space-y-1 ml-4 sm:ml-6 list-disc">
                  {slides[currentSlide].examples.slice(0, 3).map((example, idx) => (
                    <li key={idx} className="text-gray-800 leading-relaxed">
                      {example}
                    </li>
                  ))}
                </ul>
              </div>
            ) : slides[currentSlide].id === "center" ? (
              <p className="px-2 text-sm sm:text-base text-center font-bold leading-relaxed italic">
                {slides[currentSlide].centerNote}
              </p>
            ) : null}

          </div>

          {/* Progress Circles */}
          <div className="flex w-full justify-center gap-3 pt-6">
            {slides.map((slide, i) => {
              const isActive = i === currentSlide;
              const shortLabel =
                slide.id === 'left' ? 'L' :
                  slide.id === 'lean-left' ? 'LL' :
                    slide.id === 'center' ? 'C' :
                      slide.id === 'lean-right' ? 'LR' : 'R';
              return (
                <button
                  key={i}
                  onClick={() => goToSlide(i)}
                  className={`w-11 h-11 flex items-center justify-center rounded-full text-xs sm:text-sm font-semibold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400 flex-shrink-0 ${isActive
                      ? "bg-black text-white shadow-lg scale-110"
                      : `${progressBarColors[slide.color]} text-black hover:brightness-95`
                    }`}
                  role="tab"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') goToSlide(i); }}
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
      <CardFooter className="px-4 sm:px-8">
        <p className="text-sm sm:text-base font-semibold italic leading-relaxed">
          There is no news that is completely unbiased. We provide a range of perspectives on today's news to help you decide!
        </p>
      </CardFooter>

    </Card>
  );
};

export default BiasLabelGuide;
