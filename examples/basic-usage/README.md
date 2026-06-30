# Basic Usage Example

A simple Python project to demonstrate Lithic-CLI features.

## Setup

```bash
pip install lithic-cli
lithic index .
```

## Usage

```bash
# Ask about the project structure
lithic ask "What does this project do?"

# Get concise explanation
lithic explain "main.py"

# Find path between concepts
lithic path "Calculator" "greet"
```

## Project Structure

- `main.py` - Main module with Calculator class and utility functions

## Try It

```bash
# Index the project (if not done in setup)
lithic index .

# Ask questions
lithic ask "What classes are defined in main.py?"
lithic ask "What methods does Calculator have?"
```
