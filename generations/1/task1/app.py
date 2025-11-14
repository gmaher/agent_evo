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
    with open(DATA_FILE, "w") as f:
        json.dump(todos, f, indent=4)

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

def delete_todo(idx):
    todos = load_todos()
    try:
        removed_todo = todos.pop(idx - 1)
    except IndexError:
        print("Invalid todo ID")
        return
    save_todos(todos)
    print(f"Deleted todo #{idx}: {removed_todo['text']}")

def print_help():
    print("Usage:")
    print("  python app.py add \"Todo text\"")
    print("  python app.py list")
    print("  python app.py done <id>")
    print("  python app.py delete <id>")

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
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Please provide an ID.")
            return
        try:
            idx = int(sys.argv[2])
        except ValueError:
            print("ID must be an integer.")
            return
        delete_todo(idx)
    else:
        print_help()

if __name__ == "__main__":
    main()