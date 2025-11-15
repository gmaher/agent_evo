# Test Results for Tiny CLI Todo App

## Test 1: Adding a Todo
- **Command**: `python app.py add "Buy groceries"`
- **Expected Output**: `Added todo: Buy groceries`
- **Result**: Passed

## Test 2: Marking a Todo as Done
- **Command**: 
  - `python app.py done 1`
  - `python app.py list`
- **Expected Output**:
  - `Marked todo #1 as done`
  - `1. [x] Buy groceries`
- **Result**: Passed

## Test 3: Deleting a Todo
- **Command**: 
  - `python app.py delete 1`
  - `python app.py list`
- **Expected Output**:
  - `Deleted todo: Buy groceries`
  - `No todos yet.`
- **Result**: Passed

## Test 4: Handling Invalid ID for Delete
- **Command**: `python app.py delete 99`
- **Expected Output**: `Invalid todo ID`
- **Result**: Passed

## Conclusion
All tests passed successfully. The bug was fixed, and the new delete feature works as intended.