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
```

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
