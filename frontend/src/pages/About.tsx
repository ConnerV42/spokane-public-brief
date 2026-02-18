export default function About() {
  return (
    <div className="max-w-3xl space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-civic-900">About Spokane Public Brief</h1>
        <p className="mt-2 text-text-muted">
          Making local government more accessible, one meeting at a time.
        </p>
      </div>

      <section className="space-y-4 text-text leading-relaxed">
        <p>
          <strong>Spokane Public Brief</strong> is an AI-powered civic transparency tool that
          automatically collects, summarizes, and analyzes Spokane city government meetings.
        </p>
        <p>
          We pull meeting data from the Spokane City Legistar system every 6 hours, then use AI
          to generate plain-language summaries, identify high-impact agenda items, and categorize
          topics — making it easier for residents to stay informed about decisions that affect
          their community.
        </p>
      </section>

      {/* How It Works */}
      <section>
        <h2 className="text-lg font-semibold text-civic-800 mb-4">How It Works</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            {
              icon: '📥',
              title: 'Collect',
              desc: 'Every 6 hours, we scrape the official Spokane City Legistar feed for new meetings, agendas, and legislation.',
            },
            {
              icon: '🤖',
              title: 'Analyze',
              desc: 'AI reads each agenda item, generates a plain-language summary, scores community impact, and tags topics.',
            },
            {
              icon: '🔍',
              title: 'Search',
              desc: 'Browse by meeting, search by keyword, or filter by topic — all in a clean, fast interface.',
            },
          ].map((step) => (
            <div
              key={step.title}
              className="bg-surface rounded-xl border border-border p-5 shadow-sm"
            >
              <span className="text-2xl">{step.icon}</span>
              <h3 className="font-semibold text-civic-700 mt-2">{step.title}</h3>
              <p className="text-sm text-text-muted mt-1 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Data Sources */}
      <section>
        <h2 className="text-lg font-semibold text-civic-800 mb-3">Data Sources</h2>
        <ul className="list-disc list-inside space-y-1.5 text-text-muted">
          <li>
            <a
              href="https://spokanecity.legistar.com"
              className="text-civic-500 hover:text-civic-700 underline"
              target="_blank"
              rel="noopener"
            >
              Spokane City Legistar
            </a>{' '}
            — official meeting minutes, agendas, and legislation
          </li>
          <li>AI analysis via Amazon Bedrock (Claude)</li>
        </ul>
      </section>

      {/* Open Source */}
      <section>
        <h2 className="text-lg font-semibold text-civic-800 mb-3">Open Source</h2>
        <p className="text-text-muted">
          This project is fully open source. Contributions, feedback, and bug reports are
          welcome.{' '}
          <a
            href="https://github.com/ConnerV42/spokane-public-brief"
            className="text-civic-500 hover:text-civic-700 underline"
            target="_blank"
            rel="noopener"
          >
            View on GitHub →
          </a>
        </p>
      </section>

      {/* Built With */}
      <section>
        <h2 className="text-lg font-semibold text-civic-800 mb-3">Built With</h2>
        <div className="flex flex-wrap gap-2">
          {[
            'React 19',
            'Vite',
            'Tailwind CSS',
            'Python',
            'FastAPI',
            'AWS Lambda',
            'DynamoDB',
            'Amazon Bedrock',
            'Lambdaform',
          ].map((tech) => (
            <span
              key={tech}
              className="rounded-full bg-civic-50 border border-civic-200 px-3 py-1 text-xs font-medium text-civic-700"
            >
              {tech}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}
