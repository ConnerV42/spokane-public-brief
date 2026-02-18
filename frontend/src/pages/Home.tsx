import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { api, type Meeting, type AgendaItem, type Stats } from '../api/client';

/* ── Stat Card ─────────────────────────────────────────── */

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: string;
}) {
  return (
    <div className="bg-surface rounded-xl border border-border p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <p className="text-text-muted text-xs font-medium uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-civic-700 mt-0.5">{value}</p>
        </div>
      </div>
    </div>
  );
}

/* ── Search Input ──────────────────────────────────────── */

function SearchInput() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (q) navigate(`/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search meetings, agenda items, topics…"
        className="w-full rounded-xl border border-border bg-surface py-3 pl-11 pr-4 text-sm shadow-sm placeholder:text-text-muted/60 focus:outline-none focus:ring-2 focus:ring-civic-400 focus:border-civic-400 transition-all"
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
    </form>
  );
}

/* ── Meeting Card ──────────────────────────────────────── */

function MeetingCard({ meeting }: { meeting: Meeting }) {
  const date = new Date(meeting.date);
  const isUpcoming = date >= new Date();

  return (
    <Link
      to={`/meetings/${meeting.meeting_id}`}
      className="block bg-surface rounded-xl border border-border p-5 shadow-sm hover:shadow-md hover:border-civic-300 transition-all group"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-civic-800 truncate group-hover:text-civic-600 transition-colors">
              {meeting.title}
            </h3>
            {isUpcoming && (
              <span className="shrink-0 bg-accent-400/15 text-accent-500 text-[10px] font-bold uppercase px-1.5 py-0.5 rounded">
                Upcoming
              </span>
            )}
          </div>
          <p className="text-text-muted text-sm mt-1">{meeting.body_name}</p>
          {meeting.ai_summary && (
            <p className="text-text-muted text-sm mt-2 line-clamp-2">{meeting.ai_summary}</p>
          )}
        </div>
        <time className="text-xs text-text-muted whitespace-nowrap bg-civic-50 px-2.5 py-1 rounded-lg font-medium">
          {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </time>
      </div>
      {meeting.topics && meeting.topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {meeting.topics.slice(0, 4).map((t) => (
            <span
              key={t}
              className="bg-civic-100 text-civic-700 text-xs px-2 py-0.5 rounded-full font-medium"
            >
              {t}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}

/* ── Agenda Item Card (high-impact) ────────────────────── */

const impactColors = {
  high: 'bg-red-50 text-red-700 border-red-200',
  medium: 'bg-amber-50 text-amber-700 border-amber-200',
  low: 'bg-green-50 text-green-700 border-green-200',
};

function AgendaItemCard({ item }: { item: AgendaItem }) {
  const impact = item.impact_level ?? 'medium';

  return (
    <Link
      to={`/meetings/${item.meeting_id}`}
      className="block bg-surface rounded-xl border border-border p-4 shadow-sm hover:shadow-md hover:border-civic-300 transition-all"
    >
      <div className="flex items-start gap-3">
        <span
          className={`shrink-0 mt-0.5 text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${impactColors[impact]}`}
        >
          {impact}
        </span>
        <div className="min-w-0">
          <h4 className="font-medium text-civic-800 text-sm leading-snug">{item.title}</h4>
          {item.ai_analysis && (
            <p className="text-text-muted text-xs mt-1 line-clamp-2">{item.ai_analysis}</p>
          )}
          {item.topics && item.topics.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {item.topics.slice(0, 3).map((t) => (
                <span
                  key={t}
                  className="bg-civic-50 text-civic-600 text-[10px] px-1.5 py-0.5 rounded-full"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

/* ── Section Header ────────────────────────────────────── */

function SectionHeader({
  title,
  linkTo,
  linkLabel,
}: {
  title: string;
  linkTo?: string;
  linkLabel?: string;
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-lg font-semibold text-civic-800">{title}</h2>
      {linkTo && (
        <Link to={linkTo} className="text-sm text-civic-500 hover:text-civic-700 transition-colors">
          {linkLabel ?? 'View all'} →
        </Link>
      )}
    </div>
  );
}

/* ── Topic Pills ───────────────────────────────────────── */

function TopicPills({ topics }: { topics: string[] }) {
  const navigate = useNavigate();
  return (
    <div className="flex flex-wrap gap-2">
      {topics.map((topic) => (
        <button
          key={topic}
          onClick={() => navigate(`/search?q=${encodeURIComponent(topic)}`)}
          className="bg-civic-100 text-civic-700 text-xs font-medium px-3 py-1.5 rounded-full hover:bg-civic-200 transition-colors cursor-pointer"
        >
          {topic}
        </button>
      ))}
    </div>
  );
}

/* ── Loading Skeleton ──────────────────────────────────── */

function Skeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-64 bg-civic-100 rounded-lg" />
      <div className="h-4 w-96 bg-civic-50 rounded" />
      <div className="h-12 bg-civic-50 rounded-xl" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 bg-civic-50 rounded-xl" />
        ))}
      </div>
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-civic-50 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

/* ── Home Page ─────────────────────────────────────────── */

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [highImpact, setHighImpact] = useState<AgendaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.stats(),
      api.meetings(),
      api.items({ minRelevance: 4, limit: 6 }),
    ])
      .then(([s, m, itemsRes]) => {
        setStats(s);
        setMeetings(m);
        setHighImpact(itemsRes.items);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Skeleton />;

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-red-600 font-medium">Failed to load data</p>
        <p className="text-text-muted text-sm mt-1">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 text-sm text-civic-500 hover:text-civic-700 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="space-y-4">
        <h1 className="text-3xl md:text-4xl font-bold text-civic-900 tracking-tight">
          Spokane Public Brief
        </h1>
        <p className="text-text-muted max-w-xl text-base leading-relaxed">
          AI-powered summaries of Spokane city government meetings. Making civic
          information accessible, searchable, and understandable.
        </p>
        <SearchInput />
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          <StatCard icon="📋" label="Meetings" value={stats.total_meetings} />
          <StatCard icon="📌" label="Agenda Items" value={stats.total_items} />
          <StatCard icon="⚡" label="High Impact" value={stats.high_impact_count} />
          <StatCard icon="🏷️" label="Topics" value={stats.recent_topics.length} />
        </div>
      )}

      {/* Trending Topics */}
      {stats && stats.recent_topics.length > 0 && (
        <div>
          <SectionHeader title="Trending Topics" />
          <TopicPills topics={stats.recent_topics} />
        </div>
      )}

      {/* High-Impact Items */}
      {highImpact.length > 0 && (
        <div>
          <SectionHeader title="High-Impact Items" linkTo="/search" linkLabel="Search all" />
          <div className="grid md:grid-cols-2 gap-3">
            {highImpact.map((item) => (
              <AgendaItemCard key={item.item_id} item={item} />
            ))}
          </div>
        </div>
      )}

      {/* Recent Meetings */}
      <div>
        <SectionHeader title="Recent Meetings" linkTo="/search" linkLabel="Search all" />
        <div className="space-y-3">
          {meetings.slice(0, 8).map((m) => (
            <MeetingCard key={m.meeting_id} meeting={m} />
          ))}
          {meetings.length === 0 && (
            <p className="text-text-muted text-center py-8">No meetings yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
