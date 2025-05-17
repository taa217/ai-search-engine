#!/usr/bin/env python
"""
Nexus AI Search Engine - Main Entry Point
Start the advanced agentic search engine with all features.
"""
import os
import sys
import uvicorn
import logging
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal output
init()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join("logs", "nexus.log"), mode="a")
    ]
)

# Set uvicorn access logging to WARNING level to reduce verbosity
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

logger = logging.getLogger("nexus")

def print_banner():
    """Print a fancy banner to the console"""
    banner = f"""
{Fore.BLUE}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  {Fore.WHITE}███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗{Fore.BLUE}                ║
║  {Fore.WHITE}████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝{Fore.BLUE}                ║
║  {Fore.WHITE}██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗{Fore.BLUE}                ║
║  {Fore.WHITE}██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║{Fore.BLUE}                ║
║  {Fore.WHITE}██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║{Fore.BLUE}                ║
║  {Fore.WHITE}╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝{Fore.BLUE}                ║
║                                                               ║
║  {Fore.CYAN}Agentic AI Search Engine{Fore.BLUE}                                  ║
║  {Fore.CYAN}Version: 3.0.0{Fore.BLUE}                                            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def check_dependencies():
    """Check that all required dependencies are installed"""
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "langchain", 
        "langchain_openai", "openai", "aiohttp"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Please install missing packages using: pip install -r requirements.txt")
        return False
    
    return True

def check_api_keys():
    """Check if at least one LLM API key is set"""
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_gemini = bool(os.getenv("GOOGLE_API_KEY"))
    has_claude = bool(os.getenv("CLAUDE_API_KEY"))
    
    if not (has_openai or has_gemini or has_claude):
        logger.warning("No LLM API keys found. Please set at least one in your .env file.")
        logger.warning("Setting a temporary Google API key for testing purposes.")
        os.environ["GOOGLE_API_KEY"] = "AIzaSyDummyKeyForTestingPurposesOnly"
        os.environ["LLM_PROVIDER"] = "google"
        os.environ["LLM_MODEL"] = "gemini-2.5-flash-preview-04-17"
        logger.warning("Using Google/Gemini as the default provider")
    
    # Check for search API keys
    has_serpapi = bool(os.getenv("SERPAPI_API_KEY"))
    has_serper = bool(os.getenv("SERPER_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID"))
    
    if not (has_serpapi or has_serper or has_google):
        logger.warning("No search API keys found. Image search capabilities will be limited.")

def main():
    """Main entry point for the application"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Print banner
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API keys
    check_api_keys()
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Start banner
    print(f"\n{Fore.GREEN}🚀 Starting Nexus AI Search Engine on port {port}...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Press Ctrl+C to stop the server{Style.RESET_ALL}\n")
    # At the top near the MockSettings class
    print(f"DEBUG - SERPAPI_API_KEY={os.getenv('SERPAPI_API_KEY')}")
    
    # Start the server
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level="info"
    )

if __name__ == "__main__":
    main()