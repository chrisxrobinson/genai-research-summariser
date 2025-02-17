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
- Python 3.9+
- Node.js 16+
- Poetry
- Make

## Setup Instructions
1. Clone the repository
2. Install dependencies:
   ```bash
   make install-all
   ```
3. Start the development environment:
   ```bash
   make deploy
   ```

## Available Make Commands
- `make install-backend` - Install Python dependencies
- `make install-frontend` - Install Node.js dependencies
- `make install-all` - Install all dependencies
- `make build-backend` - Build backend Docker image
- `make build-frontend` - Build frontend Docker image
- `make deploy` - Start both services locally
- `make test` - Run all tests

## Development
The application runs locally at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Testing
Run the test suite with:
```bash
make test
```
