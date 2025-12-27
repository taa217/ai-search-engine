# Nexus AI Search Engine - Perplexity Backend

A clean, minimal AI search engine backend powered by [Perplexity API](https://docs.perplexity.ai/).

## Features

- 🔍 **AI-Powered Search**: Uses Perplexity's Sonar models for grounded, cited answers
- 💬 **Conversation Context**: Maintains session history for follow-up questions  
- ⚡ **Fast & Simple**: Minimal dependencies, clean architecture
- 📚 **Source Citations**: Every answer includes source URLs and snippets

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your Perplexity API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
PERPLEXITY_API_KEY=pplx-your-api-key-here
PERPLEXITY_MODEL=sonar
```

### 3. Run the Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

### `GET /` - Service Info
Returns basic service information and available models.

### `GET /health` - Health Check
Returns health status and API key configuration status.

### `POST /api/search` - Execute Search
Main search endpoint. Returns AI-generated answer with citations.

**Request:**
```json
{
  "query": "What is the latest news about AI?",
  "session_id": "optional-session-id",
  "max_results": 5,
  "model": "sonar"
}
```

**Response:**
```json
{
  "answer": "Based on recent developments...[1][2]",
  "sources": [
    {
      "index": 1,
      "url": "https://example.com/article",
      "title": "AI News Article",
      "snippet": "Recent advances in..."
    }
  ],
  "session_id": "uuid-here",
  "execution_time": 1.23,
  "model_used": "sonar",
  "related_searches": ["follow up question 1", "follow up question 2"]
}
```

### `GET /api/sessions/{session_id}` - Get Session
Returns conversation history for a session.

### `DELETE /api/sessions/{session_id}` - Delete Session
Clears a session's conversation history.

## Available Models

| Model | Description |
|-------|-------------|
| `sonar` | Fast, cost-effective search with grounding |
| `sonar-pro` | Advanced search for complex queries |
| `sonar-reasoning-pro` | Best for queries requiring reasoning |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PERPLEXITY_API_KEY` | Your Perplexity API key | Required |
| `PERPLEXITY_MODEL` | Default model to use | `sonar` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Enable debug mode | `False` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:3000` |

## Project Structure

```
backend/
├── main.py                 # FastAPI application & endpoints
├── perplexity_service.py   # Perplexity API client
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── .env.example            # Example environment file
└── README.md               # This file
```
