import json
import sys
from pathlib import Path

DATA_FILE = Path(__file__).parent / "todos.json"


def load_todos():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_todos(todos):
    # BUG: this function is never actually writing to disk correctly
    # (Hint: think about file modes / json.dump usage)
    open(DATA_FILE, "w")
    json.dumps(todos)


def list_todos():
    todos = load_todos()
    if not todos:
        print("No todos yet.")
        return
    for idx, todo in enumerate(todos, start=1):
        status = "x" if todo.get("done") else " "
        print(f"{idx}. [{status}] {todo['text']}")


def add_todo(text):
    todos = load_todos()
    todos.append({"text": text, "done": False})
    save_todos(todos)
    print(f"Added todo: {text}")


def mark_done(idx):
    todos = load_todos()
    try:
        todos[idx - 1]["done"] = True
    except IndexError:
        print("Invalid todo ID")
        return
    save_todos(todos)
    print(f"Marked todo #{idx} as done")


def print_help():
    print("Usage:")
    print("  python app.py add \"Todo text\"")
    print("  python app.py list")
    print("  python app.py done <id>")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "add":
        text = " ".join(sys.argv[2:])
        if not text:
            print("Please provide a todo text.")
            return
        add_todo(text)
    elif command == "list":
        list_todos()
    elif command == "done":
        if len(sys.argv) < 3:
            print("Please provide an ID.")
            return
        try:
            idx = int(sys.argv[2])
        except ValueError:
            print("ID must be an integer.")
            return
        mark_done(idx)
    else:
        print_help()


if __name__ == "__main__":
    main()
