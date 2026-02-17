import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router';
import { api, type SearchResult } from '../api/client';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const [input, setInput] = useState(query);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    setSearched(true);
    api
      .search(query)
      .then(setResults)
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [query]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim()) setSearchParams({ q: input.trim() });
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-civic-900">Search</h1>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search agenda items…"
          className="flex-1 border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-civic-400 focus:border-transparent"
        />
        <button
          type="submit"
          className="bg-civic-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-civic-700 transition-colors"
        >
          Search
        </button>
      </form>

      {loading && <p className="text-text-muted text-center py-8">Searching…</p>}

      {!loading && searched && results.length === 0 && (
        <p className="text-text-muted text-center py-8">No results found for "{query}"</p>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-text-muted">{results.length} results</p>
          {results.map((r) => (
            <Link
              key={r.item_id}
              to={`/meetings/${r.meeting_id}`}
              className="block bg-surface border border-border rounded-lg p-4 shadow-sm hover:shadow-md hover:border-civic-300 transition-all"
            >
              <h3 className="font-semibold text-civic-800">{r.title}</h3>
              {r.description && (
                <p className="text-text-muted text-sm mt-1 line-clamp-2">{r.description}</p>
              )}
              <div className="flex items-center gap-3 mt-2 text-xs text-text-muted">
                <span>Score: {(r.score * 100).toFixed(0)}%</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
