#!/usr/bin/env python3
"""Script to combine multiple Python files with shortened docstrings."""

import ast
import os
import sys
from typing import List, Tuple


class DocstringShortener(ast.NodeVisitor):
    """AST visitor that shortens docstrings to their first sentence."""
    
    def __init__(self):
        self.changes = []
    
    def visit_Module(self, node):
        """Process module-level docstring."""
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            docstring = node.body[0].value.value
            if isinstance(docstring, str):
                shortened = self._shorten_docstring(docstring)
                if shortened != docstring:
                    self.changes.append((node.body[0].value, shortened))
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Process class docstrings."""
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            docstring = node.body[0].value.value
            if isinstance(docstring, str):
                shortened = self._shorten_docstring(docstring)
                if shortened != docstring:
                    self.changes.append((node.body[0].value, shortened))
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Process function docstrings."""
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            docstring = node.body[0].value.value
            if isinstance(docstring, str):
                shortened = self._shorten_docstring(docstring)
                if shortened != docstring:
                    self.changes.append((node.body[0].value, shortened))
        self.generic_visit(node)
    
    def _shorten_docstring(self, docstring: str) -> str:
        """Extract the first sentence or line from a docstring."""
        # Try to get the first sentence
        docstring = docstring.strip()
        if "." in docstring:
            first_sentence = docstring.split(".", 1)[0].strip()
            if len(first_sentence) > 10:  # Ensure we have a reasonable sentence
                return first_sentence + "."
        
        # Fallback to first line if no proper sentence found
        lines = docstring.split("\n")
        return lines[0].strip()


class SourceCodeTransformer(ast.NodeTransformer):
    """AST transformer that applies docstring changes."""
    
    def __init__(self, changes):
        self.changes = changes
    
    def visit_Constant(self, node):
        """Replace docstrings with shortened versions."""
        for original_node, new_docstring in self.changes:
            if node == original_node:
                return ast.Constant(value=new_docstring)
        return node


def process_file(filepath: str) -> str:
    """Process a Python file, shortening its docstrings.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        Modified source code as string
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the source code into an AST
        tree = ast.parse(source)
        
        # Find docstrings to shorten
        shortener = DocstringShortener()
        shortener.visit(tree)
        
        # Apply the changes
        if shortener.changes:
            transformer = SourceCodeTransformer(shortener.changes)
            modified_tree = transformer.visit(tree)
            
            # Generate modified source
            modified_source = ast.unparse(modified_tree)
            return modified_source
        
        return source  # Return original if no changes
    except Exception as e:
        return f"# Error processing {filepath}: {str(e)}\n\n{source if 'source' in locals() else ''}"


def combine_files(file_paths: List[str]) -> str:
    """Combine multiple Python files into a single formatted string.
    
    Args:
        file_paths: List of paths to Python files
        
    Returns:
        Formatted string with all file contents
    """
    result = []
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            result.append(f"{file_path}:\n```\n# File not found\n```\n\n")
            continue
            
        if not file_path.endswith('.py'):
            result.append(f"{file_path}:\n```\n# Not a Python file\n```\n\n")
            continue
            
        processed_content = process_file(file_path)
        result.append(f"{file_path}:\n```\n{processed_content}\n```\n\n")
    
    return "".join(result)


def main():
    """Main function to process files from command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python script.py file1.py file2.py ...")
        sys.exit(1)
    
    file_paths = sys.argv[1:]
    output = combine_files(file_paths)
    print(output)


if __name__ == "__main__":
    main()