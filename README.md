# AI Agent Framework

A modular Python framework for creating and orchestrating tool-using AI agents and teams.

## Features

- **Tool System**: Define reusable tools with Python code that agents can execute
- **Agent Configuration**: Configure agents with custom prompts, available tools, and parameters
- **Team Orchestration**: Create teams of agents that can delegate tasks to each other
- **JSON Configuration**: Define everything through simple JSON files
- **Modular Architecture**: Clean separation of concerns with extensible components

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Quick Start

### 1. Define Tools

Create a JSON file with tool definitions:

```json
{
  "tools": [
    {
      "id": "calculator",
      "name": "calculate",
      "description": "Perform calculations",
      "parameters": [
        {
          "name": "expression",
          "type": "str",
          "description": "Math expression",
          "required": true
        }
      ],
      "returns": { "type": "float", "description": "Result" },
      "code": "def calculate(expression):\n    return eval(expression)"
    }
  ]
}
```

### 2. Define Agents

Create agents with access to specific tools:

```json
{
  "agents": [
    {
      "id": "math_agent",
      "name": "Math Expert",
      "system_prompt": "You are a math expert.",
      "tool_ids": ["calculator"],
      "model": "gpt-4"
    }
  ]
}
```

### 3. Run Single Agent

```bash
python -m agent_framework.runner \
  --tools examples/tools/basic_tools.json \
  --agents examples/agents/example_agents.json \
  --agent-id math_agent \
  --task examples/tasks/example_task.txt \
  --api-key YOUR_API_KEY
```

### 4. Run a Team

```bash
python -m agent_framework.runner \
  --tools examples/tools/basic_tools.json \
  --agents examples/agents/example_agents.json \
  --team examples/teams/example_team.json \
  --task examples/tasks/example_task.txt \
  --api-key YOUR_API_KEY
```

## Architecture

- **Models**: Data structures for Tools, Agents, and Teams
- **Core**: Execution engines for tools, agents, and teams
- **LLM**: Abstracted LLM client interface (OpenAI, Mock, etc.)
- **Loaders**: Load configurations from JSON files
- **Utils**: Parsing and utility functions

## Tool Calling Syntax

Agents use the following syntax to call tools:

```
[TOOL: tool_name(param1=value1, param2=value2)]
```

The framework automatically parses these calls, executes the tools, and returns results to the agent.

## License

MIT
