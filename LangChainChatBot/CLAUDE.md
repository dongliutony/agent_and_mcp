# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangChain-based chatbot agent that integrates weather information retrieval using LangGraph orchestration. The chatbot is named "小猪" (Little Pig) and runs interactively in the console.

## Architecture

**Core Components:**
- `agent.py`: Defines the LangChain agent with weather tool functionality
- `run.py`: Interactive console interface for multi-turn conversations
- `langgraph.json`: LangGraph configuration defining the "chatbot" graph

**Agent Architecture:**
- Uses GPT-4.1-mini as the underlying language model
- Single tool: `get_weather()` function that queries WeatherAPI.com
- Web search capability (Tavily) is implemented but currently disabled
- System prompt instructs weather-first approach for weather-related queries

## Development Commands

**Setup:**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy and fill .env file)
cp .env.example .env  # Note: .env already exists with API keys
```

**Run:**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the interactive chatbot
python run.py
# or use the full path:
.venv/bin/python run.py
```

**LangGraph Development:**
```bash
# LangGraph Studio/CLI commands (if needed)
langgraph dev  # Start development server
langgraph test  # Run tests if configured
```

## Key Implementation Details

**Weather Tool:**
- Uses WeatherAPI.com (not OpenWeatherMap as docstring suggests)
- Requires city names in English (e.g., "Beijing" not "北京")
- API endpoint: `https://api.weatherapi.com/v1/current.json`

**Environment Variables:**
- `OPENAI_API_KEY`: Required for GPT-4.1-mini model
- `OPENWEATHER_API_KEY`: Required for weather queries
- `LANGSMITH_TRACING=true`: Enables LangSmith observability
- `TAVILY_API_KEY`: Available but web search is commented out

**LangChain v1.1.0 Specifics:**
- Messages imported from `langchain_core.messages` (not `langchain.messages`)
- Agent created with `create_agent()` function
- Use `.venv/bin/python` to run with correct virtual environment

**Conversation Flow:**
- Each query creates fresh message list with system prompt
- Agent automatically handles tool calling when needed
- Exit commands: "exit" or "quit"

## Current Limitations

- No formal testing framework or test files
- No linting configuration (pylint, flake8, black, etc.)
- No build/package management (setup.py, pyproject.toml)
- Web search capability is implemented but disabled in agent tools
- Error handling is minimal - API failures may crash the application