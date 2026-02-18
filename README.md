# Spokane Public Brief

**AI-powered civic transparency for Spokane, WA.**

Spokane Public Brief automatically ingests city council and committee meeting data from Spokane's [Legistar](https://spokane.legistar.com/) system, analyzes agenda items using AI, and presents everything through a clean, searchable web interface.

> 🔬 This project also serves as a real-world QA testbed for [Lambdaform](https://github.com/ConnerV42/lambdaform) — a local Lambda development tool.

## ✨ Features

- **Automated ingestion** — Pulls meetings, agenda items, and documents from Legistar on a configurable schedule (EventBridge)
- **AI-powered analysis** — Summarizes agenda items, assesses community impact, and categorizes topics using Claude on AWS Bedrock
- **Full-text search** — Find meetings and items by keyword, filter by topic and impact level
- **Trending topics** — See what's being discussed most across recent meetings
- **Responsive frontend** — React 19 SPA with Tailwind 4, works on desktop and mobile
- **100% serverless** — Lambda + DynamoDB + API Gateway + CloudFront. No servers to manage.

## 🏗️ Architecture

```
                    ┌────────────────┐
                    │  EventBridge   │
                    │  (6h schedule) │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │   Ingestor     │──────────┐
                    │   Lambda       │          │
                    │ (Legistar API) │          │
                    └───────┬────────┘          │
                            │ SQS              │
                    ┌───────▼────────┐   ┌─────▼─────┐
                    │   Analyzer     │──▶│ DynamoDB  │
                    │   Lambda       │   │ (3 tables)│
                    │ (Bedrock AI)   │   └─────┬─────┘
                    └────────────────┘         │
                                               │
┌──────────────┐    ┌────────────────┐   ┌─────▼─────┐
│  CloudFront  │───▶│  API Gateway   │──▶│   API     │
│  + S3 (SPA)  │    │  (HTTP v2)     │   │  Lambda   │
└──────────────┘    └────────────────┘   └───────────┘
```

**Three Lambda functions:**
| Function | Purpose | Trigger |
|----------|---------|---------|
| `api` | REST API (FastAPI + Mangum) | API Gateway HTTP v2 |
| `ingestor` | Scrapes Legistar for meetings/items | EventBridge (every 6h) |
| `analyzer` | AI analysis via Bedrock Claude | SQS queue |

**DynamoDB tables:**
- `meetings` — Meeting metadata (body, date, location, agenda URL)
- `items` — Agenda items with AI analysis (summary, impact, topics)
- `metadata` — System state (last ingestion time, stats)

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- [Lambdaform](https://github.com/ConnerV42/lambdaform) (for local Lambda dev)
- AWS CLI (for deployment only)

### Local Development

```bash
# Clone
git clone https://github.com/ConnerV42/spokane-public-brief.git
cd spokane-public-brief

# Install Python dependencies
pip install -r requirements.txt

# Start the backend (Lambda emulation)
cd infra
lambdaform start
# API available at http://localhost:3000

# In another terminal — start the frontend
cd frontend
npm install
npm run dev
# Frontend available at http://localhost:5173 (proxies /api to Lambdaform)
```

### Running with DynamoDB Local

For full local development with data persistence:

```bash
# Start DynamoDB Local (requires Java)
cd dynamodb-local
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb &

# Create tables + seed data
python scripts/setup-dynamodb-local.py

# Start Lambdaform (picks up DYNAMODB_ENDPOINT from lambdaform.yaml)
cd infra
lambdaform start
```

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/meetings` | List all meetings (paginated) |
| `GET` | `/api/meetings/{id}` | Get meeting details with agenda items |
| `GET` | `/api/meetings/{id}/items` | Get agenda items for a meeting |
| `GET` | `/api/items/{id}` | Get single agenda item with AI analysis |
| `GET` | `/api/search?q=budget` | Search meetings and items by keyword |
| `GET` | `/api/stats` | Dashboard statistics (counts, trending topics) |

## 🛠️ Deployment

### Infrastructure (Terraform)

```bash
cd infra

# Initialize
terraform init

# Preview changes
terraform plan -var-file=dev.tfvars

# Deploy
terraform apply -var-file=dev.tfvars
```

### Application Code

```bash
# Build Lambda packages + frontend
./build.sh

# Update Lambda functions
aws lambda update-function-code \
  --function-name spokane-public-brief-dev-api \
  --zip-file fileb://dist/api.zip

aws lambda update-function-code \
  --function-name spokane-public-brief-dev-ingestor \
  --zip-file fileb://dist/ingestor.zip

aws lambda update-function-code \
  --function-name spokane-public-brief-dev-analyzer \
  --zip-file fileb://dist/analyzer.zip

# Deploy frontend to S3
aws s3 sync frontend/dist/ s3://spokane-public-brief-dev-frontend/ --delete
aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"
```

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite 6, Tailwind CSS 4, React Router 7 |
| **API** | FastAPI + Mangum (Lambda adapter) |
| **AI** | Claude 3.5 Sonnet via AWS Bedrock |
| **Database** | DynamoDB (3 tables) |
| **Infrastructure** | Terraform, API Gateway v2, Lambda, S3, CloudFront, EventBridge, SQS |
| **Local Dev** | [Lambdaform](https://github.com/ConnerV42/lambdaform) |

## 📁 Project Structure

```
spokane-public-brief/
├── frontend/               # React 19 SPA
│   ├── src/
│   │   ├── pages/          # Home, Search, MeetingDetail, About
│   │   ├── components/     # Layout, shared components
│   │   └── lib/            # API client
│   └── vite.config.ts
├── src/
│   └── spokane_public_brief/
│       ├── api/            # FastAPI routes
│       ├── models/         # DynamoDB data access
│       ├── ingestors/      # Legistar scraper
│       └── config.py       # Environment config
├── infra/                  # Terraform + Lambdaform config
│   ├── main.tf             # All AWS resources
│   ├── cloudfront.tf       # CDN config
│   ├── lambdaform.yaml     # Local dev config
│   └── dev.tfvars          # Dev environment vars
├── lambda_handler.py       # API Lambda entry point
├── ingestor_handler.py     # Ingestor Lambda entry point
├── analyzer_handler.py     # Analyzer Lambda entry point
├── build.sh                # Package Lambda zips + frontend
├── scripts/                # Setup helpers (DynamoDB Local)
└── tests/                  # Python tests
```

## 🤝 Contributing

Contributions welcome! This is an open-source civic transparency project.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes
4. Run tests: `python -m pytest tests/`
5. Run the app locally with Lambdaform to verify
6. Commit with a descriptive message
7. Open a Pull Request

### Development Notes

- The API Lambda uses FastAPI — add new routes in `src/spokane_public_brief/api/`
- Frontend proxies `/api` to Lambdaform in dev mode (see `vite.config.ts`)
- DynamoDB table schemas are defined in `infra/main.tf`
- AI prompts for analysis are in `src/spokane_public_brief/analyzer.py`

## ⚠️ Known Issues

- **Legistar API** returns 500 for Spokane's API endpoint — may need to scrape the web UI (`spokane.legistar.com`) instead of using the REST API
- **Bedrock access** requires `bedrock:InvokeModel` permission in the Lambda execution role

## 📄 License

[MIT](LICENSE)
