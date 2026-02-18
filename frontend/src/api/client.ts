const BASE = '/api';

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export interface Meeting {
  meeting_id: string;
  title: string;
  date: string;
  body_name: string;
  status: string;
  ai_summary?: string;
  topics?: string[];
  agenda_item_count?: number;
}

export interface AgendaItem {
  item_id: string;
  meeting_id: string;
  title: string;
  description?: string;
  impact_level?: 'high' | 'medium' | 'low';
  ai_analysis?: string;
  topics?: string[];
}

export interface Document {
  document_id: string;
  meeting_id: string;
  title: string;
  url: string;
  doc_type: string;
}

export interface SearchResult {
  item_id: string;
  title: string;
  description?: string;
  search_score: number;
  meeting_id: string;
  impact_level?: 'high' | 'medium' | 'low';
  ai_analysis?: string;
  topics?: string[];
  relevance?: number;
}

export interface SearchResponse {
  query: string;
  count: number;
  total_indexed: number;
  results: SearchResult[];
}

export interface Stats {
  total_meetings: number;
  total_items: number;
  high_impact_count: number;
  recent_topics: string[];
}

export interface ItemsResponse {
  count: number;
  items: AgendaItem[];
}

export const api = {
  health: () => fetchJSON<{ status: string }>('/health'),
  meetings: () => fetchJSON<Meeting[]>('/meetings'),
  meeting: (id: string) => fetchJSON<Meeting>(`/meetings/${id}`),
  meetingItems: (id: string) => fetchJSON<AgendaItem[]>(`/meetings/${id}/items`),
  meetingDocuments: (id: string) => fetchJSON<Document[]>(`/meetings/${id}/documents`),
  items: (opts?: { minRelevance?: number; limit?: number }) =>
    fetchJSON<ItemsResponse>(
      `/items?min_relevance=${opts?.minRelevance ?? 1}&limit=${opts?.limit ?? 50}`
    ),
  search: (q: string, limit?: number) =>
    fetchJSON<SearchResponse>(
      `/search?q=${encodeURIComponent(q)}&limit=${limit ?? 20}`
    ),
  stats: () => fetchJSON<Stats>('/stats'),
};
