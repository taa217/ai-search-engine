#!/usr/bin/env python
"""
Setup script for Nexus backend
Helps with creating directories and initial configuration
"""
import os
import sys
import shutil
from pathlib import Path

def setup_environment():
    """Set up the backend environment"""
    print("Setting up Nexus backend environment...")
    
    # Get the root directory
    root_dir = Path(__file__).parent.absolute()
    
    # Create logs directory
    logs_dir = root_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    print(f"✓ Created logs directory: {logs_dir}")
    
    # Create .env file if it doesn't exist
    env_file = root_dir / ".env"
    if not env_file.exists():
        # Check if there's a .env.example file
        env_example = root_dir / ".env.example"
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print(f"✓ Created .env file from example")
        else:
            # Create a basic .env file
            with open(env_file, "w") as f:
                f.write("""# API Settings
PORT=8000
DEBUG=True

# LLM Settings
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.2

# Vector DB Settings
VECTOR_DB=pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX=nexus-search
""")
            print(f"✓ Created basic .env file at {env_file}")
            print("⚠️  Please edit the .env file and add your API keys")
    
    # Create data directory for local vector store
    data_dir = root_dir / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"✓ Created data directory: {data_dir}")
    
    # Create a simple test file
    (data_dir / "demo.txt").write_text("This is a sample text for testing vector embeddings.")
    
    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Edit the .env file and add your API keys")
    print("2. Create a virtual environment:")
    print("   python -m venv venv")
    print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("3. Install requirements:")
    print("   pip install -r requirements.txt")
    print("4. Run the server:")
    print("   python run.py")
    
if __name__ == "__main__":
    setup_environment() 