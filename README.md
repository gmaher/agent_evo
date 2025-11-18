# Agent Evolution CLI

## Installation

```bash
# Install in development mode
pip install -e .

# Or install from package
pip install agent-evo
```

## Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-key-here"
```

Ensure MongoDB is running:

```bash
# Default connection: mongodb://localhost:27017
mongod
```

## CLI Usage

### Projects

```bash
# List all projects
evo-cli projects list --username alice

# Create a project
evo-cli projects create \
  --username alice \
  --name "My Project" \
  --description "Project description" \
  --file src/main.py \
  --file src/utils.py

# Show project details
evo-cli projects show --username alice --project-id 1

# Delete a project
evo-cli projects delete --username alice --project-id 1 --yes
```

### Agents

```bash
# List all agents
evo-cli agents list --username alice

# Show agent details
evo-cli agents show --username alice --agent-id abc123
```

### Teams

```bash
# List all teams
evo-cli teams list --username alice

# Show team details
evo-cli teams show --username alice --team-id xyz789

# Build a team automatically for a project
evo-cli teams build \
  --username alice \
  --project-id 1 \
  --temperature 0.7
```

### Runs

```bash
# List all runs
evo-cli runs list --username alice

# Filter by project
evo-cli runs list --username alice --project-id 1

# Create and execute a run
evo-cli runs create \
  --username alice \
  --project-id 1 \
  --team-id xyz789 \
  --name "My Run" \
  --max-rounds 10

# Show run details
evo-cli runs show --username alice --run-id run123
```

### Evolutions

```bash
# List all evolutions
evo-cli evolutions list --username alice

# Create and run an evolution
evo-cli evolutions create \
  --username alice \
  --project-id 1 \
  --max-rounds 5 \
  --K 4 \
  --model gpt-4o

# Show evolution details and top teams
evo-cli evolutions show --username alice --evolution-id evo123
```

## Example Workflow

```bash
# 1. Create a project
evo-cli projects create \
  --username alice \
  --name "Todo App" \
  --description "Build a REST API for a todo application" \
  --file backend/app.py \
  --file backend/models.py

# 2. Run an evolution to generate and test teams
evo-cli evolutions create \
  --username alice \
  --project-id 1 \
  --max-rounds 5 \
  --K 5

# 3. View results
evo-cli evolutions show --username alice --evolution-id <evo-id>

# 4. Run the best team again
evo-cli runs create \
  --username alice \
  --project-id 1 \
  --team-id <best-team-id>
```

## Web Interface

The web interface can be used to view and manage data created by the CLI:

```bash
# Start the web server
cd web/server
python main.py

# Or with uvicorn
uvicorn main:app --reload
```

Then open http://localhost:8000 in your browser.

## Architecture

The refactored architecture separates concerns:

- **CLI (`agent_evo/cli/`)**: User interface for all operations
- **Orchestration (`agent_evo/services/orchestration.py`)**: Business logic for complex operations
- **Repository (`agent_evo/services/repository.py`)**: Database access layer
- **Core (`agent_evo/core/`)**: Agent execution, team running, building, judging
- **Web Server (`web/server/main.py`)**: Thin HTTP API layer

All logic is in the orchestration layer, making it reusable by both CLI and web server.

````

## 8. Requirements file

```txt requirements.txt
# Core dependencies
openai>=1.0.0
pymongo>=4.0.0
pydantic>=2.0.0

# CLI dependencies
typer[all]>=0.9.0
rich>=13.0.0

# Web server dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Development
pytest>=7.4.0
black>=23.0.0
````

## Summary

The refactoring is now complete! Here's what was accomplished:

### Key Changes:

1. **Repository Layer** (`agent_evo/services/repository.py`):

   - All MongoDB operations extracted into reusable functions
   - Clean separation between data access and business logic

2. **Orchestration Layer** (`agent_evo/services/orchestration.py`):

   - All complex business logic (running teams, building teams, evolution)
   - Reusable by both CLI and web server
   - Handles LLM client initialization, team conversion, judging, etc.

3. **CLI** (`agent_evo/cli/main.py`):

   - Full-featured command-line interface using Typer
   - Rich formatting for tables and output
   - All CRUD operations plus run/evolution execution
   - Calls orchestration layer for all logic

4. **Refactored Web Server** (`web/server/main.py`):
   - Now a thin HTTP layer
   - Routes delegate to orchestration functions
   - Minimal logic - just request/response handling
   - Compatible with existing frontend

### Benefits:

- ✅ **Separation of concerns**: HTTP, business logic, and data access are separate
- ✅ **CLI-first**: All operations available via command line
- ✅ **Testable**: Orchestration layer can be tested independently
- ✅ **Reusable**: Same code powers CLI and web
- ✅ **Maintainable**: Logic in one place, not duplicated

### Usage:

```bash
# Install CLI
pip install -e .

# Use CLI
evo-cli projects list --username alice
evo-cli evolutions create --username alice --project-id 1 --max-rounds 5 --K 5

# Or use web server (same backend)
uvicorn web.server.main:app --reload
```
