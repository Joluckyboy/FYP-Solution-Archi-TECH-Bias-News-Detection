import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import get_api from "@/config/config";
import { ArrowLeft, Search } from 'lucide-react';  
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const formatDate = (value) => {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }); // e.g. 20 Feb 2026
};

const KeywordArticlesPage = () => {
  const { keyword } = useParams();
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const api = await get_api();
        const res = await axios.get(`${api}/application/articles/keyword/${keyword}`);
        setArticles(res.data.articles);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (keyword) fetchArticles();
  }, [keyword]);

  const filteredArticles = articles.filter(a =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.summary.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
        <div className="container mx-auto p-6 space-y-8">
            <div className="flex bg-white p-4 items-center gap-2">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-6 w-32" />
            </div>
            <Skeleton className="h-[200px] w-full" />
            <div className="grid grid-cols-3 gap-4">
                <Skeleton className="h-[300px]" />
                <Skeleton className="h-[300px]" />
                <Skeleton className="h-[300px]" />
            </div>
        </div>
    );
}  

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 lg:gap-8">
            {/* Left: Back Button + Title + Count */}
            <div className="flex items-center gap-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => navigate('/')}  
                className="h-8 w-8 p-0 hover:bg-slate-100"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-3xl font-bold checkmate-gradient tracking-tight">
                  Articles on <span className="text-blue-600">"{decodeURIComponent(keyword)}"</span>
                </h1>
                <p className="text-sm text-slate-500 mt-1">
                  {articles.length} articles found
                </p>
              </div>
            </div>

            {/* Right: Search Bar */}
            <div className="flex-1 max-w-md w-full lg:w-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search for articles"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 h-10 w-full"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        ) : (
          /* Article List */
          <div className="space-y-4">
            {filteredArticles.map((article, idx) => (
              <div key={idx} className="flex gap-4 p-6 bg-white rounded-xl hover:shadow-lg border border-slate-100 transition-all duration-200 items-start">
                {/* Source Icon - PLACEHOLDER VERSION */}
                <div className="h-14 w-14 rounded-full bg-gradient-to-br flex-shrink-0 overflow-hidden border-2 border-slate-200 mt-1">
                  <div className="h-full w-full flex items-center justify-center">
                    <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center border border-white/50">
                      <span className="text-xs font-bold text-white tracking-wider">
                        {article.source?.charAt(0)?.toUpperCase() || '?'}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start gap-3 mb-2">
                    <h3
                      className="font-semibold text-lg text-slate-900 hover:text-blue-600 cursor-pointer leading-snug line-clamp-2 lg:line-clamp-1 pr-2"
                      onClick={() => window.open(article.url, "_blank")}
                    >
                      {article.title}
                    </h3>
                    {article.published_at && (
                      <span className="text-xs text-slate-500 whitespace-nowrap font-medium px-2 py-1 bg-slate-100 rounded-full">
                        {formatDate(article.published_at)}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm text-slate-500 mb-3">
                    <span className="font-semibold text-slate-800">{article.source}</span>
                    <span className="text-slate-400">•</span>
                    <Badge 
                      variant="secondary" 
                      className="text-xs px-2 py-0.5 uppercase tracking-wider bg-slate-100 text-slate-700 border-slate-200"
                    >
                      {article.political_bias || 'Unknown'}
                    </Badge>
                  </div>
                  
                  <p className="text-slate-600 text-sm leading-relaxed line-clamp-3">
                    {article.summary}
                  </p>
                </div>
              </div>
            ))}
            
            {filteredArticles.length === 0 && !loading && (
              <div className="text-center py-20 text-slate-500 bg-white rounded-xl border-2 border-dashed border-slate-200">
                <Search className="mx-auto h-12 w-12 text-slate-400 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  No articles found
                </h3>
                <p className="text-sm">
                {searchQuery 
                  ? `No articles match ${searchQuery}, please try something else!` 
                  : `No articles match ${decodeURIComponent(keyword)}</span>".`
                }
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

};

export default KeywordArticlesPage;
