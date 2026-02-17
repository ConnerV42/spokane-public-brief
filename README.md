# Spokane Public Brief

AI-powered civic transparency for Spokane, WA.

Spokane Public Brief automatically ingests city council and committee meeting data from Spokane's [Legistar](https://spokane.legistar.com/) system, analyzes agenda items using AI (Claude on AWS Bedrock), and presents everything through a clean, searchable web interface.

## Features

- **Automated ingestion** — Pulls meetings, agenda items, and documents from Legistar on a schedule
- **AI analysis** — Summarizes agenda items, assesses community impact, and categorizes topics using Claude on Bedrock
- **Keyword search** — Find meetings and items by topic
- **Serverless architecture** — Runs entirely on AWS Lambda + DynamoDB + API Gateway

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌───────────┐
│ EventBridge  │────▶│  Ingestor    │────▶│ DynamoDB  │
│ (6h schedule)│     │  Lambda      │     │           │
└──────────────┘     └──────┬───────┘     └─────┬─────┘
                            │                   │
                     ┌──────▼───────┐           │
                     │  Analyzer    │───────────┘
                     │  Lambda      │
                     │  (Bedrock)   │
                     └──────────────┘
                                          ┌─────┴─────┐
┌──────────────┐     ┌──────────────┐     │ DynamoDB  │
│  CloudFront  │────▶│  API Gateway │────▶│           │
│  + S3 (SPA)  │     │  (HTTP v2)  │     └───────────┘
└──────────────┘     └──────────────┘
```

## Local Development

This project uses [Lambdaform](https://github.com/ConnerV42/lambdaform) for local Lambda development.

```bash
# Install dependencies
pip install -r requirements.txt

# Start local dev server
cd infra
lambdaform start

# In another terminal
curl http://localhost:3000/api/meetings
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/meetings` | List all meetings |
| GET | `/api/meetings/{id}` | Get meeting details |
| GET | `/api/meetings/{id}/items` | Get agenda items for a meeting |
| GET | `/api/items/{id}` | Get agenda item details |
| GET | `/api/search?q=...` | Search meetings and items |
| GET | `/api/stats` | Dashboard statistics |

## Deployment

```bash
# Set up AWS credentials
export AWS_PROFILE=your-profile

# Deploy infrastructure
cd infra
terraform init
terraform apply -var-file=dev.tfvars
```

## Tech Stack

- **Runtime:** Python 3.12
- **AI:** Claude 3.5 Sonnet via AWS Bedrock
- **Database:** DynamoDB
- **API:** FastAPI + Mangum (Lambda adapter)
- **Infrastructure:** Terraform
- **Frontend:** React 19 + Vite 6 + Tailwind 4 (coming soon)

## License

MIT
