# Tiny CLI Todo App

This is a minimal command-line todo list application.

## Features

- Add todos
- List todos
- Mark todos as done ✅ (BUG fixed: the done status now persists correctly)
- Delete todos by ID

## Requirements

- Python 3.10+
- No external dependencies

## Usage

```bash
python app.py add "Buy milk"
python app.py add "Finish report"
python app.py list
python app.py done 1
python app.py list
python app.py delete 1
python app.py list
```

## Change Log

- **Bug Fix**: Fixed the issue where marking a todo as done did not persist after restarting the program.
- **New Feature**: Added `delete <id>` command to remove a todo by its 1-based ID.