# GenAI Research Summariser

A web application that aggregates and summarizes the latest generative AI research papers using OpenAI and LangChain, presenting them in a blog-like interface.

## Features
- Automated research paper aggregation
- AI-powered summarization using OpenAI
- Blog-style presentation of research summaries
- RESTful API built with FastAPI
- React-based frontend
- AWS Lambda deployment ready

## Repository Structure
```
genai-research-summarizer/
├── backend/                     # Python FastAPI backend
│   ├── app/                     # Application code
│   ├── pyproject.toml          # Poetry dependencies
│   └── Dockerfile              # Backend container definition
├── frontend/                    # React frontend
│   ├── src/                    # React components
│   └── Dockerfile              # Frontend container definition
├── terraform/                   # Infrastructure as Code
├── docker-compose.yml          # Local development setup
└── Makefile                    # Build and deployment commands
```

## Prerequisites
- Docker and Docker Compose
- Python 3.12+
- Node.js 16+
- Poetry
- Make

## Local Development Setup

### Quick Start

The easiest way to get started is using our convenience `make` commands:

```bash
# Install all dependencies, build containers and initialize local environment
make setup

# Or step by step:
make install-all  # Install dependencies
make build        # Build Docker images
make local-init   # Initialize local environment
```

After running these commands, the application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/docs

### Manual Setup

If you prefer to set up manually:

1. Clone the repository
2. Install backend dependencies:
   ```bash
   cd backend
   poetry install
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
4. Start the Docker containers:
   ```bash
   docker-compose up -d
   ```

### Local Development Environment

The local setup includes:
- **Backend**: FastAPI application running on port 8001
- **Frontend**: React application running on port 3000
- **DynamoDB Local**: DynamoDB emulator on port 8000
- **LocalStack**: Provides S3 emulation on port 4566

All storage is ephemeral and will be reset when containers are removed.

## Available Make Commands

### Development
- `make up` - Start all services in detached mode
- `make down` - Stop all services
- `make logs` - View logs from all services
- `make setup` - Complete setup (install, build, initialize)
- `make local-init` - Initialize local environment

### Build & Installation
- `make build` - Build all Docker images
- `make install-backend` - Install Python dependencies
- `make install-frontend` - Install Node.js dependencies
- `make install-all` - Install all dependencies

### Testing & Code Quality
- `make test` - Run all tests
- `make lint` - Run linting checks
- `make fmt` - Format code
- `make check` - Run all checks (lint + test)

### Maintenance
- `make docker-clean` - Clean Docker resources
- `make docker-image-prune` - Remove unused Docker images

## Making API Requests

Once the services are running, you can interact with the API:

```bash
# Upload a document
curl -X POST "http://localhost:8001/api/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/research-paper.pdf" \
  -F "title=Example Research Paper" \
  -F "document_type=RESEARCH_PAPER"

# List all documents
curl "http://localhost:8001/api/documents"
```

## Testing
Run the test suite with:
```bash
make test
```
