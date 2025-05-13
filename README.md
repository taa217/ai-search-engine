# Nexus AI Search Engine

A high-performance, agentic AI search engine that combines real-time web search with advanced AI synthesis capabilities. Built for production environments with scalability and reliability in mind.

## Features

- **Advanced AI Search**: Combines multiple search sources with LLM reasoning for comprehensive results
- **Real-time Web Search**: Integrates with search engines and Wikipedia for up-to-date information
- **Async Architecture**: Built with FastAPI and async I/O for high throughput and performance
- **Intelligent Caching**: Efficient response caching to reduce latency and API costs
- **Scalable Design**: Built to handle thousands of concurrent users
- **Fallback Mechanisms**: Graceful degradation when services are unavailable
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Environment Configuration**: Simple environment-based configuration

## Project Structure

```
nexus-ai-search/
├── backend/                  # Backend API service
│   ├── src/                  # Source code
│   │   ├── agents/           # AI agent implementations
│   │   ├── utils/            # Utility modules
│   │   └── main.py           # API entry point
│   ├── logs/                 # Log files
│   ├── .env                  # Environment variables (create from .env.example)
│   ├── .env.example          # Example environment file
│   └── requirements.txt      # Python dependencies
└── README.md                 # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key (or alternative LLM API)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nexus-ai-search.git
   cd nexus-ai-search
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Running the API

Start the development server:

```bash
cd backend
uvicorn src.main_super:app --reload
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
  "query": "What is quantum computing?",
  "max_results": 5,
  "use_web": true,
  "depth": 2,
  "use_ai_synthesis": true,
  "search_type": "comprehensive"
}
```

Response:

```json
{
  "results": [
    {
      "content": "Quantum computing is a type of computation that harnesses quantum mechanical phenomena such as superposition and entanglement to perform operations on data. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or qubits, which can exist in multiple states simultaneously. This allows quantum computers to solve certain complex problems exponentially faster than classical computers, particularly in areas like cryptography, optimization, and quantum physics simulations.",
      "type": "text"
    }
  ],
  "reasoning": [
    {
      "step": 1,
      "thought": "Analyzed query to determine it's seeking a definition and explanation of quantum computing"
    },
    {
      "step": 2,
      "thought": "Retrieved information from multiple sources including academic and educational websites"
    },
    {
      "step": 3,
      "thought": "Synthesized information to provide a comprehensive yet concise explanation"
    }
  ],
  "sources": [
    {
      "title": "Quantum Computing - IBM",
      "link": "https://www.ibm.com/quantum-computing/",
      "snippet": "Quantum computing harnesses the phenomena of quantum mechanics to deliver a huge leap forward in computation."
    }
  ],
  "execution_time": 0.857
}
```

## Configuration

The application can be configured using environment variables. See `.env.example` for all available options.

## Scaling for Production

For production deployments:

1. Use a production ASGI server:
   ```bash
   uvicorn src.main_super:app --host 0.0.0.0 --port 8000 --workers 4
   ```

2. Consider using a reverse proxy like Nginx

3. Implement a distributed cache with Redis

4. Deploy with Docker and container orchestration:
   ```bash
   docker build -t nexus-ai-search .
   docker run -p 8000:8000 --env-file .env nexus-ai-search
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
