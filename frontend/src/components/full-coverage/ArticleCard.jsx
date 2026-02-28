import { Copy } from "lucide-react";

const ArticleCard = ({ article, idx, copiedIdx, handleCopy }) => {
    const SG_DOMAINS = {
        "channel newsasia": "channelnewsasia.com",
        "the straits times": "straitstimes.com",
        "today online": "todayonline.com",
        "the business times": "businesstimes.com.sg",
        "mothership": "mothership.sg",
        "yahoo news singapore": "sg.yahoo.com",
    };

    const getSourceIcon = (source) => {
        const key = source?.toLowerCase().trim();
        const domain = SG_DOMAINS[key] ?? `${key?.replace(/\s+/g, '')}.com`;
        return `https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http://${domain}&size=32`;
    };

    const getBiasLabel = (rawBias) => {
        return { label: rawBias || "Unknown", color: "bg-slate-200 text-slate-700" };
    };

    const biasLabel = getBiasLabel(article.political_bias || article.bias);

    return (
        <div className="flex gap-4 p-4 bg-white rounded-lg hover:shadow-md transition-shadow border border-slate-100 items-start">
            {/* Logo */}
            <div className="h-12 w-12 rounded-full bg-slate-100 flex-shrink-0 overflow-hidden border border-slate-200">
                <img
                    src={getSourceIcon(article.source)}
                    alt={article.source}
                    className="h-full w-full object-contain"
                    onError={(e) => { e.target.style.display = "none"; }}
                />
            </div>

            <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-lg text-slate-900 hover:text-blue-600 cursor-pointer leading-tight"
                    onClick={() => window.open(article.url, '_blank')}>
                    {article.title}
                </h3>

                <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className="font-medium text-slate-700 text-sm">{article.source}</span>
                    <span className="text-slate-300">•</span>
                    <span className={`px-2 py-0.5 rounded-full text-[11px] uppercase ${biasLabel.color}`}>
                        {biasLabel.label}
                    </span>
                </div>

                {article.summary && (
                    <p className="text-slate-600 mt-2 text-sm line-clamp-2">{article.summary}</p>
                )}
            </div>

            {/* Copies URL */}
            <button
                className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded hover:bg-slate-100 transition-colors"
                title={copiedIdx === idx ? "Copied!" : "Copy link"}
                onClick={() => handleCopy(article.url, idx)}
            >
                {copiedIdx === idx
                    ? <span className="text-green-500 text-xs font-bold">✓</span>
                    : <Copy className="h-4 w-4 text-slate-400 hover:text-slate-600" />
                }
            </button>
        </div>
    );
};

export default ArticleCard;
