# Nexus AI Search Engine

A high-performance, agentic AI search engine that combines real-time web search with multiple AI models for synthesis.

## Features

- **Multiple AI Model Support**: Use OpenAI, Google's Gemini, or Anthropic's Claude models
- **Real-time Web Search**: Integrates with DuckDuckGo and Wikipedia for up-to-date information
- **Async Architecture**: Built with FastAPI and async I/O for high throughput
- **Intelligent Caching**: Efficient response caching to reduce latency and API costs
- **Detailed Reasoning**: Shows step-by-step thinking behind search results

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys
   ```

## API Keys

You need at least one of these API keys to use the service:

- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/account/api-keys)
- **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Anthropic Claude API Key**: Get from [Anthropic Console](https://console.anthropic.com/account/keys)

## Running the API

Use the advanced script to run with multi-model support:

```bash
python run_advanced.py --reload
```

The API will be available at http://localhost:8000.

## API Usage

### Search Endpoint

```http
POST /api/search
```

Request body:

```json
{
  "query": "latest advancements in quantum computing",
  "max_results": 5,
  "model": "gemini"  // Can be "openai", "gemini", or "claude"
}
```

If no model is specified, it will use the `DEFAULT_MODEL` from your .env file.

### Response Format

```json
{
  "results": [
    {
      "content": "Comprehensive answer synthesized by AI...",
      "type": "text"
    }
  ],
  "reasoning": [
    {
      "step": 1,
      "thought": "First analyzed the query to understand..."
    },
    {
      "step": 2, 
      "thought": "Then searched through multiple sources..."
    }
  ],
  "sources": [
    {
      "title": "Recent Advances in Quantum Computing",
      "link": "https://example.com/quantum-advances",
      "snippet": "Researchers have made significant progress in..."
    }
  ],
  "execution_time": 0.75,
  "model_used": "gemini"
}
```

## Models Comparison

Each model has its own strengths:

- **OpenAI (GPT)**: Comprehensive knowledge, excellent reasoning
- **Gemini**: Excellent at interpreting factual information, strong with technical content
- **Claude**: Strong reasoning capabilities, good with nuanced interpretations

## Troubleshooting

If you encounter issues:

1. Verify your API keys are correctly set in the `.env` file
2. Check API quota limits for the respective services
3. Ensure you're using valid model names as specified in the documentation