"""In-memory filesystem for storing files without disk I/O."""

from typing import Dict, Optional
from pathlib import Path


class FileSystem:
    """In-memory filesystem that stores files in a dictionary."""
    
    def __init__(self):
        """Initialize an empty filesystem."""
        self.files: Dict[str, str] = {}
    
    def read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read the contents of a file from memory."""
        # Normalize path
        file_path = str(Path(file_path))
        
        # Check if file exists
        if file_path not in self.files:
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Return the file content
        content = self.files[file_path]
        return f"Successfully read {len(content)} characters from {file_path}\n\nContent:\n{content}"
    
    def write_file(self, file_path: str, content: str, mode: str = "w", encoding: str = "utf-8") -> str:
        """Write content to a file in memory."""
        # Normalize path
        file_path = str(Path(file_path))
        
        # Validate mode
        if mode not in ['w', 'a']:
            raise ValueError(f"Invalid mode: {mode}. Use 'w' for write or 'a' for append")
        
        # Write or append
        if mode == 'w':
            self.files[file_path] = content
            action = "overwrote"
        else:  # mode == 'a'
            if file_path in self.files:
                self.files[file_path] += content
            else:
                self.files[file_path] = content
            action = "appended to"
        
        bytes_written = len(content)
        return f"Successfully {action} {file_path}. Wrote {bytes_written} characters."
    
    def exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        file_path = str(Path(file_path))
        return file_path in self.files
    
    def list_files(self) -> list[str]:
        """List all files in the filesystem."""
        return sorted(self.files.keys())
    
    def get_directory_structure(self, ignored_files: Optional[set] = None) -> str:
        """Get a tree-like representation of the filesystem."""
        if ignored_files is None:
            ignored_files = set()
        
        # Build directory tree
        tree = {}
        for file_path in self.files.keys():
            if any(ignored in file_path for ignored in ignored_files):
                continue
            
            parts = Path(file_path).parts
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            # Add file
            current[parts[-1]] = None
        
        # Format tree
        def format_tree(node: dict, prefix: str = "", is_last: bool = True) -> list[str]:
            lines = []
            items = sorted(node.items())
            for i, (name, subtree) in enumerate(items):
                is_last_item = i == len(items) - 1
                current_prefix = "└── " if is_last_item else "├── "
                next_prefix = "    " if is_last_item else "│   "
                
                if subtree is None:
                    # It's a file
                    lines.append(f"{prefix}{current_prefix}{name}")
                else:
                    # It's a directory
                    lines.append(f"{prefix}{current_prefix}{name}/")
                    lines.extend(format_tree(subtree, prefix + next_prefix, is_last_item))
            return lines
        
        if not tree:
            return "(empty filesystem)"
        
        return "\n".join(format_tree(tree))
    
    def clear(self):
        """Clear all files from the filesystem."""
        self.files.clear()