import { useEffect, useState, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router';
import { api, type SearchResult } from '../api/client';

/* ── Impact badge colors ───────────────────────────────── */

const impactColors = {
  high: 'bg-red-50 text-red-700 border-red-200',
  medium: 'bg-amber-50 text-amber-700 border-amber-200',
  low: 'bg-green-50 text-green-700 border-green-200',
};

/* ── Search Result Card ────────────────────────────────── */

function ResultCard({ result }: { result: SearchResult }) {
  const impact = result.impact_level ?? 'low';
  const scorePercent = Math.round(result.search_score * 100);

  return (
    <Link
      to={`/meetings/${result.meeting_id}`}
      className="block bg-surface rounded-xl border border-border p-5 shadow-sm hover:shadow-md hover:border-civic-300 transition-all group"
    >
      <div className="flex items-start gap-3">
        <span
          className={`shrink-0 mt-0.5 text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${impactColors[impact]}`}
        >
          {impact}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-civic-800 text-sm leading-snug group-hover:text-civic-600 transition-colors">
            {result.title}
          </h3>
          {result.description && (
            <p className="text-text-muted text-sm mt-1.5 line-clamp-2 leading-relaxed">
              {result.description}
            </p>
          )}
          {result.ai_analysis && !result.description && (
            <p className="text-text-muted text-sm mt-1.5 line-clamp-2 leading-relaxed italic">
              {result.ai_analysis}
            </p>
          )}
          <div className="flex items-center flex-wrap gap-2 mt-3">
            {result.topics && result.topics.length > 0 && (
              <>
                {result.topics.slice(0, 3).map((t) => (
                  <span
                    key={t}
                    className="bg-civic-50 text-civic-600 text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                  >
                    {t}
                  </span>
                ))}
              </>
            )}
            <span className="ml-auto text-[11px] text-text-muted font-medium tabular-nums">
              {scorePercent}% match
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}

/* ── Topic Filter Chips ────────────────────────────────── */

function TopicChips({
  topics,
  active,
  onToggle,
}: {
  topics: string[];
  active: Set<string>;
  onToggle: (topic: string) => void;
}) {
  if (topics.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {topics.map((topic) => {
        const isActive = active.has(topic);
        return (
          <button
            key={topic}
            onClick={() => onToggle(topic)}
            className={`text-xs font-medium px-3 py-1.5 rounded-full transition-colors cursor-pointer ${
              isActive
                ? 'bg-civic-600 text-white shadow-sm'
                : 'bg-civic-100 text-civic-700 hover:bg-civic-200'
            }`}
          >
            {topic}
          </button>
        );
      })}
      {active.size > 0 && (
        <button
          onClick={() => active.forEach((t) => onToggle(t))}
          className="text-xs text-text-muted hover:text-civic-600 px-2 py-1.5 transition-colors cursor-pointer"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}

/* ── Loading Skeleton ──────────────────────────────────── */

function SearchSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="h-24 bg-civic-50 rounded-xl" />
      ))}
    </div>
  );
}

/* ── Search Page ───────────────────────────────────────── */

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const [input, setInput] = useState(query);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalIndexed, setTotalIndexed] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [activeTopics, setActiveTopics] = useState<Set<string>>(new Set());
  const [trendingTopics, setTrendingTopics] = useState<string[]>([]);

  // Fetch trending topics for suggestions
  useEffect(() => {
    api.stats().then((s) => setTrendingTopics(s.topics)).catch(() => {});
  }, []);

  // Run search when query changes
  useEffect(() => {
    if (!query) {
      setResults([]);
      setSearched(false);
      return;
    }
    setLoading(true);
    setSearched(true);
    setActiveTopics(new Set());
    api
      .search(query, 50)
      .then((res) => {
        setResults(res.results);
        setTotalIndexed(res.total_indexed);
      })
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [query]);

  // Sync input with URL query
  useEffect(() => {
    setInput(query);
  }, [query]);

  // Extract unique topics from results
  const resultTopics = useMemo(() => {
    const topicCounts = new Map<string, number>();
    results.forEach((r) => {
      r.topics?.forEach((t) => topicCounts.set(t, (topicCounts.get(t) ?? 0) + 1));
    });
    return [...topicCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12)
      .map(([t]) => t);
  }, [results]);

  // Filter results by active topics
  const filteredResults = useMemo(() => {
    if (activeTopics.size === 0) return results;
    return results.filter((r) =>
      r.topics?.some((t) => activeTopics.has(t))
    );
  }, [results, activeTopics]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (q) setSearchParams({ q });
  }

  function handleTopicToggle(topic: string) {
    setActiveTopics((prev) => {
      const next = new Set(prev);
      if (next.has(topic)) next.delete(topic);
      else next.add(topic);
      return next;
    });
  }

  function handleTopicSearch(topic: string) {
    setSearchParams({ q: topic });
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-civic-900">Search</h1>
        <p className="text-text-muted text-sm mt-1">
          Find agenda items across all Spokane city meetings
        </p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search agenda items, topics, descriptions…"
          className="w-full rounded-xl border border-border bg-surface py-3 pl-11 pr-28 text-sm shadow-sm placeholder:text-text-muted/60 focus:outline-none focus:ring-2 focus:ring-civic-400 focus:border-civic-400 transition-all"
        />
        <svg
          className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-text-muted"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-civic-600 text-white px-5 py-1.5 rounded-lg text-sm font-medium hover:bg-civic-700 transition-colors"
        >
          Search
        </button>
      </form>

      {/* Trending topics (when no query) */}
      {!query && trendingTopics.length > 0 && (
        <div>
          <p className="text-xs font-medium text-text-muted uppercase tracking-wide mb-2">
            Trending topics
          </p>
          <div className="flex flex-wrap gap-2">
            {trendingTopics.map((topic) => (
              <button
                key={topic}
                onClick={() => handleTopicSearch(topic)}
                className="bg-civic-100 text-civic-700 text-xs font-medium px-3 py-1.5 rounded-full hover:bg-civic-200 transition-colors cursor-pointer"
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && <SearchSkeleton />}

      {/* Results */}
      {!loading && searched && (
        <div className="space-y-4">
          {/* Results meta */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-text-muted">
              {filteredResults.length === results.length ? (
                <>
                  <span className="font-medium text-civic-700">{results.length}</span>{' '}
                  {results.length === 1 ? 'result' : 'results'} for "{query}"
                </>
              ) : (
                <>
                  <span className="font-medium text-civic-700">{filteredResults.length}</span>{' '}
                  of {results.length} results (filtered)
                </>
              )}
            </p>
            {totalIndexed > 0 && (
              <p className="text-xs text-text-muted">
                {totalIndexed} items indexed
              </p>
            )}
          </div>

          {/* Topic filter chips from results */}
          {resultTopics.length > 0 && results.length > 0 && (
            <div>
              <p className="text-xs font-medium text-text-muted uppercase tracking-wide mb-2">
                Filter by topic
              </p>
              <TopicChips
                topics={resultTopics}
                active={activeTopics}
                onToggle={handleTopicToggle}
              />
            </div>
          )}

          {/* Result cards */}
          {filteredResults.length > 0 ? (
            <div className="space-y-3">
              {filteredResults.map((r) => (
                <ResultCard key={r.item_id} result={r} />
              ))}
            </div>
          ) : results.length > 0 ? (
            <div className="text-center py-12">
              <p className="text-text-muted">No results match the selected topics</p>
              <button
                onClick={() => setActiveTopics(new Set())}
                className="mt-2 text-sm text-civic-500 hover:text-civic-700 underline"
              >
                Clear filters
              </button>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-2xl mb-2">🔍</p>
              <p className="text-civic-700 font-medium">No results found</p>
              <p className="text-text-muted text-sm mt-1">
                Try different keywords or browse{' '}
                <Link to="/" className="text-civic-500 hover:text-civic-700 underline">
                  recent meetings
                </Link>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Empty state (no query yet) */}
      {!loading && !searched && !query && (
        <div className="text-center py-16">
          <p className="text-4xl mb-3">🏛️</p>
          <p className="text-civic-700 font-medium">Search Spokane city government</p>
          <p className="text-text-muted text-sm mt-1 max-w-md mx-auto">
            Find agenda items, resolutions, and discussions from city council
            and committee meetings.
          </p>
        </div>
      )}
    </div>
  );
}
