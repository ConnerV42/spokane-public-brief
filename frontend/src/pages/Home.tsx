import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { api, type Meeting, type Stats } from '../api/client';

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-surface rounded-xl border border-border p-5 shadow-sm">
      <p className="text-text-muted text-sm font-medium">{label}</p>
      <p className="text-3xl font-bold text-civic-700 mt-1">{value}</p>
    </div>
  );
}

function MeetingCard({ meeting }: { meeting: Meeting }) {
  return (
    <Link
      to={`/meetings/${meeting.meeting_id}`}
      className="block bg-surface rounded-xl border border-border p-5 shadow-sm hover:shadow-md hover:border-civic-300 transition-all"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="font-semibold text-civic-800 truncate">{meeting.title}</h3>
          <p className="text-text-muted text-sm mt-1">{meeting.body_name}</p>
          {meeting.ai_summary && (
            <p className="text-text-muted text-sm mt-2 line-clamp-2">{meeting.ai_summary}</p>
          )}
        </div>
        <time className="text-xs text-text-muted whitespace-nowrap bg-civic-50 px-2 py-1 rounded">
          {new Date(meeting.date).toLocaleDateString()}
        </time>
      </div>
      {meeting.topics && meeting.topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {meeting.topics.slice(0, 4).map((t) => (
            <span key={t} className="bg-civic-100 text-civic-700 text-xs px-2 py-0.5 rounded-full">
              {t}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.stats(), api.meetings()])
      .then(([s, m]) => {
        setStats(s);
        setMeetings(m);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-text-muted text-center py-12">Loading…</p>;
  if (error) return <p className="text-red-600 text-center py-12">Error: {error}</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-civic-900">Spokane Public Brief</h1>
        <p className="text-text-muted mt-2">
          AI-powered summaries of Spokane city government meetings, making civic information
          accessible to everyone.
        </p>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Meetings" value={stats.total_meetings} />
          <StatCard label="Agenda Items" value={stats.total_items} />
          <StatCard label="High Impact" value={stats.high_impact_count} />
          <StatCard label="Topics" value={stats.recent_topics.length} />
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-civic-800">Recent Meetings</h2>
          <Link to="/search" className="text-sm text-civic-500 hover:text-civic-700">
            Search all →
          </Link>
        </div>
        <div className="space-y-3">
          {meetings.slice(0, 10).map((m) => (
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
