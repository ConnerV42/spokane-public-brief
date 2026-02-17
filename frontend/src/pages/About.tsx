export default function About() {
  return (
    <div className="max-w-2xl space-y-8">
      <h1 className="text-2xl font-bold text-civic-900">About</h1>

      <div className="space-y-4 text-text leading-relaxed">
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
      </div>

      <div>
        <h2 className="text-lg font-semibold text-civic-800 mb-3">Data Sources</h2>
        <ul className="list-disc list-inside space-y-1 text-text-muted">
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
      </div>

      <div>
        <h2 className="text-lg font-semibold text-civic-800 mb-3">Open Source</h2>
        <p className="text-text-muted">
          This project is fully open source.{' '}
          <a
            href="https://github.com/ConnerV42/spokane-public-brief"
            className="text-civic-500 hover:text-civic-700 underline"
            target="_blank"
            rel="noopener"
          >
            View on GitHub →
          </a>
        </p>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-civic-800 mb-3">Built With</h2>
        <ul className="list-disc list-inside space-y-1 text-text-muted">
          <li>React 19 + Vite + Tailwind CSS</li>
          <li>Python + FastAPI (serverless on AWS Lambda)</li>
          <li>DynamoDB for storage</li>
          <li>Local development powered by <a href="https://github.com/ConnerV42/lambdaform" className="text-civic-500 hover:text-civic-700 underline" target="_blank" rel="noopener">Lambdaform</a></li>
        </ul>
      </div>
    </div>
  );
}
