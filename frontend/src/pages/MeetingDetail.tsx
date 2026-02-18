import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router';
import { api, type Meeting, type AgendaItem, type Document } from '../api/client';

/* ── Impact Badge ──────────────────────────────────────── */

const impactConfig: Record<string, { bg: string; dot: string; label: string }> = {
  high: { bg: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500', label: 'High Impact' },
  medium: { bg: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500', label: 'Medium' },
  low: { bg: 'bg-green-50 text-green-700 border-green-200', dot: 'bg-green-500', label: 'Low' },
};

function ImpactBadge({ level }: { level?: string }) {
  const cfg = impactConfig[level ?? ''];
  if (!cfg) return null;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${cfg.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

/* ── Status Badge ──────────────────────────────────────── */

function StatusBadge({ status }: { status: string }) {
  const isFinalized = status === 'final' || status === 'finalized';
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${
        isFinalized
          ? 'bg-green-50 text-green-700 border border-green-200'
          : 'bg-blue-50 text-blue-700 border border-blue-200'
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${isFinalized ? 'bg-green-500' : 'bg-blue-500'}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

/* ── Document Type Icon ────────────────────────────────── */

function DocIcon({ type }: { type: string }) {
  const icons: Record<string, string> = {
    minutes: '📝',
    agenda: '📋',
    attachment: '📎',
    report: '📊',
    ordinance: '⚖️',
    resolution: '🏛️',
  };
  return <span className="text-xl">{icons[type.toLowerCase()] ?? '📄'}</span>;
}

/* ── Loading Skeleton ──────────────────────────────────── */

function Skeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Back link */}
      <div className="h-4 w-16 bg-civic-100 rounded" />
      {/* Title */}
      <div className="space-y-3">
        <div className="h-8 w-3/4 bg-civic-100 rounded-lg" />
        <div className="flex gap-3">
          <div className="h-5 w-24 bg-civic-50 rounded-full" />
          <div className="h-5 w-20 bg-civic-50 rounded-full" />
          <div className="h-5 w-16 bg-civic-50 rounded-full" />
        </div>
      </div>
      {/* AI Summary */}
      <div className="bg-civic-50 rounded-xl p-5 space-y-2">
        <div className="h-5 w-28 bg-civic-100 rounded" />
        <div className="h-4 w-full bg-civic-100/60 rounded" />
        <div className="h-4 w-5/6 bg-civic-100/60 rounded" />
        <div className="h-4 w-2/3 bg-civic-100/60 rounded" />
      </div>
      {/* Items */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-civic-50 rounded-xl p-5 space-y-2">
          <div className="h-5 w-2/3 bg-civic-100 rounded" />
          <div className="h-4 w-full bg-civic-100/50 rounded" />
        </div>
      ))}
    </div>
  );
}

/* ── Meeting Detail Page ───────────────────────────────── */

export default function MeetingDetail() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [items, setItems] = useState<AgendaItem[]>([]);
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    Promise.all([api.meeting(id), api.meetingItems(id), api.meetingDocuments(id)])
      .then(([m, i, d]) => {
        setMeeting(m);
        setItems(i);
        setDocs(d);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Skeleton />;

  if (error) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-red-600 font-medium text-lg">Failed to load meeting</p>
        <p className="text-text-muted text-sm">{error}</p>
        <div className="flex items-center justify-center gap-4 pt-2">
          <Link to="/" className="text-sm text-civic-500 hover:text-civic-700 underline">
            ← Back to home
          </Link>
          <button
            onClick={() => window.location.reload()}
            className="text-sm bg-civic-600 text-white px-4 py-2 rounded-lg hover:bg-civic-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="text-center py-16 space-y-3">
        <p className="text-2xl">🔍</p>
        <p className="text-text-muted font-medium">Meeting not found</p>
        <Link to="/" className="text-sm text-civic-500 hover:text-civic-700 underline">
          ← Back to home
        </Link>
      </div>
    );
  }

  const meetingDate = new Date(meeting.date);
  const isUpcoming = meetingDate >= new Date();

  // Sort items: high impact first
  const sortedItems = [...items].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return (order[a.impact_level ?? 'low'] ?? 2) - (order[b.impact_level ?? 'low'] ?? 2);
  });

  const highCount = items.filter((i) => i.impact_level === 'high').length;
  const medCount = items.filter((i) => i.impact_level === 'medium').length;

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-civic-500 hover:text-civic-700 transition-colors group"
      >
        <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
        Back to meetings
      </Link>

      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-start gap-3 flex-wrap">
          <h1 className="text-2xl md:text-3xl font-bold text-civic-900 tracking-tight leading-tight">
            {meeting.title}
          </h1>
          {isUpcoming && (
            <span className="shrink-0 mt-1 bg-accent-400/15 text-accent-500 text-xs font-bold uppercase px-2 py-1 rounded">
              Upcoming
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="bg-civic-100 text-civic-700 px-3 py-1 rounded-full font-medium">
            {meeting.body_name}
          </span>
          <time className="text-text-muted font-medium">
            {meetingDate.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </time>
          <StatusBadge status={meeting.status} />
        </div>

        {/* Topics */}
        {meeting.topics && meeting.topics.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {meeting.topics.map((t) => (
              <Link
                key={t}
                to={`/search?q=${encodeURIComponent(t)}`}
                className="bg-civic-50 text-civic-600 text-xs px-2.5 py-1 rounded-full hover:bg-civic-100 transition-colors"
              >
                {t}
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* AI Summary */}
      {meeting.ai_summary && (
        <div className="bg-gradient-to-br from-civic-50 to-white border border-civic-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">✨</span>
            <h2 className="font-semibold text-civic-800">AI Summary</h2>
          </div>
          <p className="text-text leading-relaxed">{meeting.ai_summary}</p>
        </div>
      )}

      {/* Quick Stats Bar */}
      {items.length > 0 && (
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2 bg-surface border border-border rounded-lg px-4 py-2.5">
            <span className="text-lg">📌</span>
            <span className="text-text-muted">Agenda Items</span>
            <span className="font-bold text-civic-700">{items.length}</span>
          </div>
          {highCount > 0 && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-2.5">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-red-700">High Impact</span>
              <span className="font-bold text-red-800">{highCount}</span>
            </div>
          )}
          {medCount > 0 && (
            <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-amber-700">Medium</span>
              <span className="font-bold text-amber-800">{medCount}</span>
            </div>
          )}
          {docs.length > 0 && (
            <div className="flex items-center gap-2 bg-surface border border-border rounded-lg px-4 py-2.5">
              <span className="text-lg">📄</span>
              <span className="text-text-muted">Documents</span>
              <span className="font-bold text-civic-700">{docs.length}</span>
            </div>
          )}
        </div>
      )}

      {/* Agenda Items */}
      <div>
        <h2 className="text-xl font-semibold text-civic-800 mb-4">
          Agenda Items
        </h2>
        {sortedItems.length === 0 ? (
          <p className="text-text-muted bg-civic-50 rounded-xl p-6 text-center">
            No agenda items available for this meeting.
          </p>
        ) : (
          <div className="space-y-3">
            {sortedItems.map((item, idx) => (
              <div
                key={item.item_id}
                className="bg-surface border border-border rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0">
                    <span className="shrink-0 text-text-muted text-sm font-mono mt-0.5 w-6 text-right">
                      {idx + 1}.
                    </span>
                    <h3 className="font-medium text-civic-800 leading-snug">{item.title}</h3>
                  </div>
                  <ImpactBadge level={item.impact_level} />
                </div>

                {item.description && (
                  <p className="text-text-muted text-sm mt-2 ml-9">{item.description}</p>
                )}

                {item.ai_analysis && (
                  <div className="mt-3 ml-9 bg-gradient-to-br from-civic-50 to-white border border-civic-100 rounded-lg p-4">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="text-sm">✨</span>
                      <p className="font-medium text-civic-700 text-sm">AI Analysis</p>
                    </div>
                    <p className="text-text text-sm leading-relaxed">{item.ai_analysis}</p>
                  </div>
                )}

                {item.topics && item.topics.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3 ml-9">
                    {item.topics.map((t) => (
                      <Link
                        key={t}
                        to={`/search?q=${encodeURIComponent(t)}`}
                        className="bg-civic-50 text-civic-600 text-[11px] px-2 py-0.5 rounded-full hover:bg-civic-100 transition-colors"
                      >
                        {t}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Documents */}
      {docs.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-civic-800 mb-4">Source Documents</h2>
          <div className="grid md:grid-cols-2 gap-3">
            {docs.map((d) => (
              <a
                key={d.document_id}
                href={d.url}
                target="_blank"
                rel="noopener"
                className="flex items-center gap-3 bg-surface border border-border rounded-xl p-4 shadow-sm hover:shadow-md hover:border-civic-300 transition-all group"
              >
                <DocIcon type={d.doc_type} />
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-civic-700 group-hover:text-civic-600 transition-colors truncate">
                    {d.title}
                  </p>
                  <p className="text-xs text-text-muted capitalize">{d.doc_type}</p>
                </div>
                <span className="text-text-muted text-xs shrink-0 group-hover:translate-x-0.5 transition-transform">
                  ↗
                </span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
