# AgentEvo - Evolutionary AI Team Factory

A framework for creating, evolving, and optimizing AI agent teams through evolutionary algorithms. The system uses meta-teams (builder teams) to generate task-specific agent teams, evaluates their performance, and evolves better builders through selective merging.

## 🎯 Core Concept

**AgentEvo** implements an evolutionary approach to AI team optimization:

1. **Builder Teams** create task-specific agent teams
2. Generated teams solve reference tasks
3. Performance is evaluated by an LLM judge
4. Best-performing builders are merged to create improved versions
5. Repeat to evolve increasingly effective team factories

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Evolutionary Workflow](#evolutionary-workflow)
- [Configuration](#configuration)
- [Contributing](#contributing)

## 🚀 Installation

### Prerequisites

- Python 3.8+
- OpenAI API key

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd agent-evo

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

## ⚡ Quick Start

### 1. Prepare Reference Tasks

Create a directory with subdirectories, each containing a `task.txt`:

```
tasks/
├── task1/
│   └── task.txt
├── task2/
│   └── task.txt
└── task3/
    └── task.txt
```

### 2. Build Teams for All Tasks

```bash
python scripts/build_batch.py \
  --tasks-dir tasks/ \
  --builder-dir teams/team2 \
  --model gpt-4o \
  --max-rounds 10
```

This creates a `team/` subdirectory in each task folder with:

- `tools.json` - Custom tools for the team
- `agents.json` - Agent definitions
- `team.json` - Team structure and delegation graph

### 3. Run Teams on Tasks

```bash
python scripts/run_batch.py \
  --tasks-dir tasks/ \
  --model gpt-4o \
  --max-rounds 10
```

This executes each team on its task and saves results to `output.json` in each task folder.

### 4. Evaluate Performance

```bash
python scripts/evaluate_batch.py \
  --tasks-dir tasks/ \
  --model gpt-4o
```

Generates `evaluation.json` with scores (0-10) and reasoning for each task.

### 5. Merge Best Performers

```bash
python scripts/merge_teams.py \
  --team1-dir tasks/task1/team \
  --team2-dir tasks/task3/team \
  --output-dir teams/merged_team \
  --model gpt-4o
```

Creates an improved team by combining strengths of high-performing builders.

## 🧠 Core Concepts

### Teams

A **Team** is a directed graph of agents that can delegate work to each other:

```json
{
  "id": "example_team",
  "name": "Example Team",
  "description": "A team that solves problems",
  "agent_ids": ["analyst", "executor", "reviewer"],
  "edges": [
    {
      "from": "analyst",
      "to": "executor",
      "description": "Delegates implementation"
    },
    { "from": "executor", "to": "reviewer", "description": "Requests review" }
  ],
  "entry_point": "analyst"
}
```

**Key Properties:**

- **Entry Point**: First agent to receive the task
- **Edges**: Define who can delegate to whom
- **Directed Graph**: Work flows along edges

### Agents

An **Agent** is an AI with a specific role, system prompt, and available tools:

```json
{
  "id": "analyst",
  "name": "Task Analyst",
  "system_prompt": "You analyze tasks and break them into steps...",
  "tool_ids": ["web_search", "file_reader"],
  "temperature": 0.7
}
```

**Default Tools** (always available):

- `read_file` - Read file contents
- `write_file` - Write/append to files

### Tools

**Tools** are Python functions agents can execute:

```json
{
  "id": "web_search",
  "name": "search_web",
  "description": "Search the web for information",
  "parameters": [
    {
      "name": "query",
      "type": "string",
      "description": "Search query",
      "required": true
    }
  ],
  "returns": {
    "type": "string",
    "description": "Search results"
  },
  "code": "def search_web(query: str) -> str:\n    ..."
}
```

### Execution Flow

```
┌─────────────┐
│ Entry Agent │ ← Receives initial task
└──────┬──────┘
       │ Uses tools, makes progress
       ↓
┌──────────────┐
│ [DELEGATE]   │ → Passes subtask to another agent
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Next Agent   │ ← Continues work
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ <FINISHED>   │ ← Marks completion
└──────────────┘
```

**Agent Actions:**

1. **Use tools** - Execute functions to make progress
2. **Delegate** - Use `[DELEGATE: agent_id] task description`
3. **Finish** - Use `<FINISHED>` when done

## 📁 Project Structure

```
agent-evo/
├── agent_evo/
│   ├── core/
│   │   ├── app.py              # Main application class
│   │   ├── team_runner.py      # Orchestrates team execution
│   │   ├── agent_runner.py     # Runs individual agents
│   │   ├── tool_executor.py    # Executes tool code safely
│   │   ├── evaluator.py        # Evaluates team performance
│   │   └── merger.py           # Merges two teams
│   ├── models/
│   │   ├── agent.py            # Agent data model
│   │   ├── team.py             # Team data model
│   │   ├── tool.py             # Tool data model
│   │   └── default_tools.py    # Default tools (read/write)
│   ├── llm/
│   │   └── client.py           # LLM client wrapper
│   ├── loaders/
│   │   └── json_loader.py      # Load teams from JSON
│   ├── utils/
│   │   └── parser.py           # Parse tool calls from responses
│   └── prompts/
│       ├── agent.py            # Agent system prompts
│       ├── builder.py          # Builder team prompts
│       ├── judge.py            # Evaluation prompts
│       └── merge.py            # Merge prompts
├── scripts/
│   ├── build_batch.py          # Build teams for multiple tasks
│   ├── run_batch.py            # Run teams on tasks
│   ├── evaluate_batch.py       # Evaluate results
│   └── merge_teams.py          # Merge two teams
├── teams/
│   └── team2/                  # Example builder team
│       ├── tools.json
│       ├── agents.json
│       └── team.json
└── constants/
    └── template/tasks/         # Reference task templates
```

## 📖 Usage Guide

### Building Teams

**Single Task:**

```python
from agent_evo.core.app import AgentEvoApp

app = AgentEvoApp(model="gpt-4o", output_dir="./output")

# Load builder team
builder_config = app.load_team_from_directory("teams/team2")

# Build team for a task
with open("task.txt", "r") as f:
    task = f.read()

result = app.run_team(
    team=builder_config['team'],
    task=f"Create an AI team to solve: {task}",
    agents=builder_config['agents'],
    tools=builder_config['tools'],
    max_rounds=10
)
```

**Batch Processing:**

```bash
python scripts/build_batch.py \
  --tasks-dir constants/template/tasks \
  --builder-dir teams/team2 \
  --model gpt-4o \
  --verbose
```

### Running Teams

**Single Task:**

```python
app = AgentEvoApp(model="gpt-4o")

result = app.run_from_directory(
    team_dir="tasks/task1/team",
    task_path="tasks/task1/task.txt",
    max_rounds=10
)

print(f"Completed in {result['rounds']} rounds")
```

**Batch Processing:**

```bash
python scripts/run_batch.py \
  --tasks-dir tasks/ \
  --model gpt-4o \
  --max-rounds 15
```

### Evaluating Results

```python
from agent_evo.core.evaluator import TeamEvaluator
from agent_evo.llm.client import OpenAIClient
import json

llm_client = OpenAIClient(api_key="...", model="gpt-4o")
evaluator = TeamEvaluator(llm_client)

with open("tasks/task1/task.txt") as f:
    task = f.read()

with open("tasks/task1/output.json") as f:
    result = json.load(f)

evaluation = evaluator.evaluate(
    task=task,
    result=result,
    additional_files=["tasks/task1/app.py", "tasks/task1/README.md"]
)

print(f"Score: {evaluation['score']}/10")
print(f"Reasoning: {evaluation['reasoning']}")
```

### Merging Teams

```python
from agent_evo.core.merger import TeamMerger
from agent_evo.llm.client import OpenAIClient

llm_client = OpenAIClient(api_key="...", model="gpt-4o")
merger = TeamMerger(llm_client)

result = merger.merge_teams(
    team1_dir="tasks/task1/team",
    team2_dir="tasks/task2/team",
    output_dir="teams/merged",
    verbose=True
)

print(f"Created files: {result['validation']['created_files']}")
```

## 🔄 Evolutionary Workflow

### Complete Evolution Cycle

TODO

### Fitness Metrics

Teams are evaluated on:

- **Task Completion** (0-10 scale)
- **Tool Usage** (efficiency)
- **Delegation Logic** (appropriate handoffs)
- **Output Quality** (judged by LLM)

### Selection Strategy

**Recommended approach:**

1. Run 5-10 reference tasks per generation
2. Select top 2-3 teams (score ≥ 8/10)
3. Merge in pairs or triple-merge best performers
4. Create multiple merged variants
5. Test on new task variations

## ⚙️ Configuration

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional
export OPENAI_BASE_URL="https://api.openai.com/v1"  # For custom endpoints
```

### Model Selection

All scripts support `--model` parameter:

```bash
# Use different models
--model gpt-4o          # Balanced (default)
--model gpt-4-turbo     # More capable
--model gpt-3.5-turbo   # Faster, cheaper
```

### Team Configuration

**Ignored Files** (excluded from directory context):

```python
app = AgentEvoApp(
    ignored_files=["agents.json", "tools.json", "team.json", ".git", "__pycache__"]
)
```

## 🤝 Contributing

### Creating a Builder Team

1. **Define Tools** (`tools.json`):

```json
{
  "tools": [
    {
      "id": "my_tool",
      "name": "my_function",
      "description": "What it does",
      "parameters": [...],
      "returns": {...},
      "code": "def my_function(...):\n    ..."
    }
  ]
}
```

2. **Define Agents** (`agents.json`):

```json
{
  "agents": [
    {
      "id": "specialist",
      "name": "Task Specialist",
      "system_prompt": "You are expert at...",
      "tool_ids": ["my_tool"],
      "temperature": 0.7
    }
  ]
}
```

3. **Define Team Structure** (`team.json`):

```json
{
  "id": "my_team",
  "name": "My Team",
  "description": "What this team does",
  "agent_ids": ["agent1", "agent2"],
  "edges": [{ "from": "agent1", "to": "agent2" }],
  "entry_point": "agent1"
}
```

### Adding Reference Tasks

Create tasks that test different capabilities:

**Good task properties:**

- **Specific** - Clear success criteria
- **Measurable** - Objective evaluation possible
- **Diverse** - Tests different skills (file ops, research, analysis)
- **Realistic** - Real-world scenarios

**Example task.txt:**

```markdown
# Task: Debug and Enhance Todo App

Fix the persistence bug where completed todos don't save.
Add a delete command.
Update documentation.

Success criteria:

- Todos persist after restart
- Delete command works correctly
- README.md is updated
```

### Testing

```bash
# Test individual components
python -m pytest tests/

# Test full pipeline
python scripts/build_batch.py --tasks-dir test_tasks --builder-dir teams/team2
python scripts/run_batch.py --tasks-dir test_tasks
python scripts/evaluate_batch.py --tasks-dir test_tasks
```

## 🐛 Troubleshooting

### Common Issues

**"Missing required files"**

- Ensure `tools.json`, `agents.json`, `team.json` exist
- Check JSON syntax with `python -m json.tool < file.json`

**"Agent delegation cycle detected"**

- Review team edges - ensure no infinite loops
- Entry point should have path to completion

**"Tool execution failed"**

- Check tool code syntax: `python -c "exec(tool_code)"`
- Verify all imports are available
- Test with simple arguments first

**Low evaluation scores**

- Increase `--max-rounds` for complex tasks
- Review agent system prompts for clarity
- Check if agents have necessary tools

### Debug Mode

Enable verbose output:

```bash
python scripts/run_batch.py \
  --tasks-dir tasks/ \
  --verbose
```

## 📊 Evaluation Criteria

The LLM judge evaluates based on:

1. **Completeness** - All task requirements met
2. **Correctness** - Solutions work as specified
3. **Quality** - Code/output follows best practices
4. **Documentation** - Changes are documented
5. **Efficiency** - Minimal unnecessary iterations

**Scoring Guide:**

- **9-10**: Exceptional, production-ready
- **7-8**: Good, minor improvements needed
- **5-6**: Partial completion, significant gaps
- **3-4**: Major issues, limited progress
- **0-2**: Failed to complete task

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

Built with:

- OpenAI GPT models for agent intelligence
- Python for flexibility and ease of use
- JSON for human-readable configurations

---

**Happy Evolving! 🧬🤖**

For questions or issues, please open a GitHub issue or reach out to the maintainers.
