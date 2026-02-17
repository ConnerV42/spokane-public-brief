import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router';
import { api, type Meeting, type AgendaItem, type Document } from '../api/client';

function ImpactBadge({ level }: { level?: string }) {
  const colors: Record<string, string> = {
    high: 'bg-red-100 text-red-800',
    medium: 'bg-amber-100 text-amber-800',
    low: 'bg-green-100 text-green-800',
  };
  if (!level) return null;
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors[level] ?? 'bg-gray-100 text-gray-600'}`}>
      {level}
    </span>
  );
}

export default function MeetingDetail() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [items, setItems] = useState<AgendaItem[]>([]);
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([api.meeting(id), api.meetingItems(id), api.meetingDocuments(id)])
      .then(([m, i, d]) => {
        setMeeting(m);
        setItems(i);
        setDocs(d);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-text-muted text-center py-12">Loading…</p>;
  if (error) return <p className="text-red-600 text-center py-12">Error: {error}</p>;
  if (!meeting) return <p className="text-text-muted text-center py-12">Meeting not found.</p>;

  return (
    <div className="space-y-8">
      <div>
        <Link to="/" className="text-sm text-civic-500 hover:text-civic-700">← Back</Link>
        <h1 className="text-2xl font-bold text-civic-900 mt-2">{meeting.title}</h1>
        <div className="flex flex-wrap gap-3 text-sm text-text-muted mt-2">
          <span>{meeting.body_name}</span>
          <span>·</span>
          <time>{new Date(meeting.date).toLocaleDateString()}</time>
          <span>·</span>
          <span className="capitalize">{meeting.status}</span>
        </div>
      </div>

      {meeting.ai_summary && (
        <div className="bg-civic-50 border border-civic-200 rounded-xl p-5">
          <h2 className="font-semibold text-civic-800 mb-2">AI Summary</h2>
          <p className="text-text leading-relaxed">{meeting.ai_summary}</p>
        </div>
      )}

      {meeting.topics && meeting.topics.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {meeting.topics.map((t) => (
            <span key={t} className="bg-civic-100 text-civic-700 text-sm px-3 py-1 rounded-full">{t}</span>
          ))}
        </div>
      )}

      <div>
        <h2 className="text-xl font-semibold text-civic-800 mb-4">
          Agenda Items ({items.length})
        </h2>
        {items.length === 0 ? (
          <p className="text-text-muted">No agenda items.</p>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={item.item_id}
                className="bg-surface border border-border rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-medium text-civic-800">{item.title}</h3>
                  <ImpactBadge level={item.impact_level} />
                </div>
                {item.description && (
                  <p className="text-text-muted text-sm mt-2">{item.description}</p>
                )}
                {item.ai_analysis && (
                  <div className="mt-3 bg-civic-50 rounded p-3 text-sm">
                    <p className="font-medium text-civic-700 mb-1">AI Analysis</p>
                    <p className="text-text">{item.ai_analysis}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {docs.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-civic-800 mb-4">Documents</h2>
          <div className="space-y-2">
            {docs.map((d) => (
              <a
                key={d.document_id}
                href={d.url}
                target="_blank"
                rel="noopener"
                className="flex items-center gap-3 bg-surface border border-border rounded-lg p-3 hover:border-civic-300 transition-colors"
              >
                <span className="text-xl">📄</span>
                <div>
                  <p className="font-medium text-civic-700">{d.title}</p>
                  <p className="text-xs text-text-muted">{d.doc_type}</p>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
