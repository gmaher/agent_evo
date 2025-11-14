# Tiny CLI Todo App

This is a minimal command-line todo list application.

## Features

- Add todos
- List todos
- Mark todos as done ✅

## Requirements

- Python 3.10+
- No external dependencies

## Usage

```bash
python app.py add "Buy milk"
python app.py add "Finish report"
python app.py list
python app.py done 1
python app.py delete 1
python app.py list
```

## Change Log

- **Bug Fix:** Fixed the persistence issue where marking todos as done did not persist after restarting the program.
- **New Feature:** Added a `delete <id>` command to remove todos by their ID, with graceful handling of invalid IDs.