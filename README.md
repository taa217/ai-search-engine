# Nexus AI Search Engine

A high-performance, agentic AI search engine powered by the Perplexity API. It combines real-time web search with advanced AI synthesis capabilities, offering both fast standard searches and deep agentic research modes.

## Features

- **Perplexity Integration**: Powered by state-of-the-art Perplexity models (sonar, sonar-pro).
- **Real-time Web Search**: Up-to-the-minute information retrieval.
- **Streaming Responses**: Server-Sent Events (SSE) for real-time answer generation.
- **Agentic Research Mode**: Deep dive capabilities with multi-step reasoning (using `sonar-pro`).
- **Multi-modal Support**: Handles text and image search results.
- **Session Management**: Maintains conversation context for follow-up queries.
- **Vercel Ready**: Configured for easy serverless deployment on Vercel.

## Project Structure

```
nexus-ai-search/
├── backend/                  # FastAPI Backend
│   ├── main.py               # API Entry point & Application definition
│   ├── perplexity_service.py # Perplexity API integration logic
│   ├── .env                  # Environment variables
│   ├── .env.example          # Example environment configuration
│   ├── requirements.txt      # Python dependencies
│   └── vercel.json           # Vercel deployment configuration
├── frontend/                 # React Frontend
└── README.md                 # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.9+
- Perplexity API Key

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-search-engine
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Unix/MacOS
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your `PERPLEXITY_API_KEY`.

### Running the API

Start the development server:

```bash
cd backend
python main.py
# OR
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Usage

### Streaming Search (Standard)

```http
POST /api/search/stream
```

**Body:**
```json
{
  "query": "latest developments in fusion energy",
  "session_id": "optional-uuid",
  "model_name": "sonar"
}
```

**Response:** Server-Sent Events (SSE) stream containing JSON chunks with content updates and final sources.

### Agentic Search (Deep Research)

```http
POST /agentic-search
```

**Body:**
```json
{
  "query": "comprehensive analysis of quantum computing market",
  "session_id": "optional-uuid"
}
```

**Response:** JSON object containing a research plan, synthesis, and sources.

## Deployment

### Deploying to Vercel

The backend is configured for Vercel deployment using `vercel.json`.

1. Install Vercel CLI: `npm i -g vercel`
2. Run deployment from the root or backend directory:
   ```bash
   vercel
   ```
3. Set the `PERPLEXITY_API_KEY` in your Vercel project settings.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
