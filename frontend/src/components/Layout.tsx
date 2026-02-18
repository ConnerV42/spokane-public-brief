import { Link, Outlet, useLocation } from 'react-router';

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/search', label: 'Search' },
  { to: '/about', label: 'About' },
];

export default function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-civic-800 focus:text-white focus:px-4 focus:py-2 focus:rounded"
      >
        Skip to content
      </a>
      <header className="bg-civic-800 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🏛️</span>
            <span className="font-bold text-lg tracking-tight">Spokane Public Brief</span>
          </Link>
          <nav aria-label="Main navigation" className="flex gap-6 text-sm font-medium">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`hover:text-civic-200 transition-colors ${
                  pathname === item.to ? 'text-white underline underline-offset-4' : 'text-civic-300'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main id="main-content" className="flex-1 max-w-6xl mx-auto px-4 py-8 w-full">
        <Outlet />
      </main>

      <footer className="bg-civic-900 text-civic-400 text-sm py-6">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p>Spokane Public Brief — AI-powered civic transparency</p>
          <p className="mt-1">
            Open source on{' '}
            <a
              href="https://github.com/ConnerV42/spokane-public-brief"
              className="underline hover:text-white"
              target="_blank"
              rel="noopener"
            >
              GitHub
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
