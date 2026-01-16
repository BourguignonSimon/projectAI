# Silent Factory

An AI-powered multi-agent workflow orchestration system that automates the software development lifecycle. Multiple specialized AI agents collaborate to transform user requirements into production code.

## Overview

Silent Factory uses a team of AI agents that communicate through Redis Streams to orchestrate the entire development process:

```
User Request -> Manager -> Analyst -> Architect -> Coder -> Reviewer -> Output
                  ^                                            |
                  |____________________________________________|
                              (Feedback Loop)
```

### Agents

| Agent | Role | Model |
|-------|------|-------|
| **Manager** | Orchestrates workflow and delegates tasks | gemini-2.5-pro |
| **Analyst** | Extracts requirements and specifications | gemini-2.5-pro |
| **Architect** | Designs system architecture and file structure | gemini-2.5-pro |
| **Coder** | Generates production code | gemini-2.5-flash |
| **Reviewer** | Audits code quality and provides feedback | gemini-2.5-flash |

## Prerequisites

- Python 3.8+
- Redis server (Docker recommended)
- Google Gemini API key

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/BourguignonSimon/projectAI.git
   cd projectAI
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Start Redis** (using Docker)
   ```bash
   docker run -d --name redis-lab -p 6380:6379 redis:latest
   ```

## Usage

### Start the Factory

```bash
./start_wsl.sh
```

This will:
- Start all agent processes in the background
- Launch the client terminal for user interaction
- Create necessary directories (`logs/`, `livrables/`, `project_logs/`)

### Interact with Agents

Use the client terminal to submit requests. Agents communicate using mentions:
- `@Manager` - Direct the workflow orchestrator
- `@Analyst` - Request requirements analysis
- `@Architect` - Request system design
- `@Coder` - Request code generation
- `@Reviewer` - Request code review

### Reset the System

```bash
./reset_factory.sh
```

## Project Structure

```
projectAI/
├── agent_manager.py      # Manager agent (orchestrator)
├── agent_generic.py      # Generic agent runner for specialized roles
├── client_terminal.py    # User terminal interface
├── utils.py              # Shared utilities (Redis, AI, logging)
├── start_wsl.sh          # Startup script
├── reset_factory.sh      # Reset script
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
│
├── logs/                 # Agent runtime logs
├── project_logs/         # Project execution history (JSONL)
└── livrables/            # Generated code artifacts
```

## Configuration

Environment variables (`.env`):

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | `AIza...` |
| `REDIS_HOST` | Redis server hostname | `localhost` |
| `REDIS_PORT` | Redis server port | `6380` |
| `MODEL_SMART` | Model for complex tasks | `gemini-2.5-pro` |
| `MODEL_FAST` | Model for quick tasks | `gemini-2.5-flash` |

## Architecture

### Communication Flow

All agents communicate asynchronously through a Redis Stream (`table_ronde_stream`). Messages include:
- `request_id` - Unique project identifier
- `sequence_id` - Message ordering within a project
- `sender` - Agent that sent the message
- `content` - Message payload
- `type` - Message type (message, command, etc.)
- `status` - Processing status

### Context Management

The system uses intelligent context compression to manage token usage:
1. Recent messages are kept in full
2. Older messages are compressed into a technical summary
3. Compression threshold: 8+ messages triggers summarization

## Development

### Install development dependencies

```bash
pip install -r requirements-dev.txt
```

### Code Quality

```bash
# Format code
black .

# Check linting
flake8

# Sort imports
isort .
```

### Running Tests

```bash
pytest
```

## License

This project is proprietary software. All rights reserved.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.
