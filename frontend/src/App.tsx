import { BrowserRouter, Routes, Route } from 'react-router';
import Layout from './components/Layout';
import Home from './pages/Home';
import MeetingDetail from './pages/MeetingDetail';
import Search from './pages/Search';
import About from './pages/About';
import { Link } from 'react-router';

function NotFound() {
  return (
    <div className="text-center py-16 space-y-3">
      <p className="text-4xl">🏛️</p>
      <h1 className="text-2xl font-bold text-civic-900">Page Not Found</h1>
      <p className="text-text-muted">The page you're looking for doesn't exist.</p>
      <Link to="/" className="inline-block mt-2 text-sm text-civic-500 hover:text-civic-700 underline">
        ← Back to home
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="meetings/:id" element={<MeetingDetail />} />
          <Route path="search" element={<Search />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
