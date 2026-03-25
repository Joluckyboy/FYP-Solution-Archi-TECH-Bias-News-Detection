import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import get_api from "@/config/config";
import { ArrowLeft, Search } from 'lucide-react';  
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from "lucide-react";
import ArticleCard from '@/components/full-coverage/ArticleCard';

const KeywordArticlesPage = () => {
  const { keyword } = useParams();
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [copiedIdx, setCopiedIdx] = useState(null);

  const handleCopy = (url, idx) => {
    navigator.clipboard.writeText(url).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    });
  };

  useEffect(() => {
    const fetchArticles = async (kw) => {
      try {
        setLoading(true);
        const api = await get_api();
        const res = await axios.get(`${api}/application/articles/keyword/${kw}`);
        setArticles(res.data.articles);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (keyword) fetchArticles(decodeURIComponent(keyword));
  }, [keyword]);

  useEffect(() => {
    const timer = setTimeout(() => {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'smooth'
      });
    }, 100);
    
    return () => clearTimeout(timer);
  }, [keyword]);

  const handleNewSearch = (e) => {
    e.preventDefault();
    const trimmed = searchKeyword.trim();
    if (trimmed) {
      navigate(`/keywords/${encodeURIComponent(trimmed)}`, { replace: true });
    }
  };

  const filteredArticles = articles.filter(a =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.summary.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
      <Loader2 className="h-10 w-10 animate-spin text-primary" />
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
                onClick={() => {
                  navigate('/', { replace: true });
                  setTimeout(() => {
                    const footer = document.getElementById('page-footer');
                    footer?.scrollIntoView({ 
                      behavior: 'smooth', 
                      block: 'end' 
                    });
                  }, 1500);
                }}
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
            <form onSubmit={handleNewSearch} className="mb-6">
              <div className="flex-1 max-w-md w-full lg:w-auto">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search new keyword..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="pl-10 pr-4 h-10 w-full"
                    enterKeyHint="search"
                  />
                </div>
              </div>
            </form>
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
              <ArticleCard
                key={idx}
                article={article}
                idx={idx}
                copiedIdx={copiedIdx}
                handleCopy={handleCopy}
              />
            ))}
            
            {filteredArticles.length === 0 && !loading && (
              <div className="text-center py-20 text-slate-500 bg-white rounded-xl border-2 border-dashed border-slate-200">
                <Search className="mx-auto h-12 w-12 text-slate-400 mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  No articles found
                </h3>
                <p className="text-sm">
                {searchQuery 
                  ? `We can’t find any results related to "${decodeURIComponent(keyword)}" and "${searchQuery}"!` 
                  : `We can’t find any relevant articles for "${decodeURIComponent(keyword)}". Please try again by refining your keyword(s)!`
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
