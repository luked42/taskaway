# TaskAway

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://github.com/python/mypy)
[![Checked with flake8](https://img.shields.io/badge/flake8-checked-blue.svg)](https://github.com/pycqa/flake8)
[![CI](https://github.com/luked42/taskaway/actions/workflows/ci.yml/badge.svg)](https://github.com/luked42/taskaway/actions/workflows/ci.yml)

TaskAway is a terminal user interface for TaskWarrior, providing an intuitive and efficient way to manage your tasks. It offers a modern, keyboard-driven interface with features like:

- Project-based task organization
- Tag management
- Task filtering
- Task annotations
- Column layout customization
- Theme support

## Installation

TaskAway can be installed using Poetry:

```bash
poetry add taskaway
```

Or clone the repository and install in development mode:

```bash
git clone https://github.com/luked42/taskaway.git
cd taskaway
poetry install
```

## Usage

Run TaskAway with:

```bash
taskaway
```

### Command Line Arguments

- `--task_config`: Path to TaskWarrior config file (default: ~/.task)
- `--taskaway_config`: Path to TaskAway config file (default: ~/.taskaway.json)
- `--task_command`: Command to run TaskWarrior (default: task)

## Key Bindings

- `j/k`: Move cursor down/up
- `g/G`: Move to top/bottom
- `l`: Configure column layout
- `escape`: Clear filters
- `d`: Mark task complete
- `t`: Add tag to task
- `a`: Add task
- `A`: Add annotation
- `p`: Modify project
- `m`: Modify task
- `P`: Filter for highlighted project
- `T`: Filter for highlighted tags
- `q`: Quit and save
- `ctrl+t`: Change theme
- `e`: Edit task
- `b`: Toggle start/stop
- `h`: Toggle help

## Development

### Prerequisites

- Python 3.9 or higher
- Poetry for dependency management
- TaskWarrior installed on your system

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/luked42/taskaway.git
cd taskaway
```

2. Install dependencies:
```bash
poetry install
```

3. Install pre-commit hooks:
```bash
poetry run pre-commit install
```

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

The project uses Black for code formatting. To format all files:

```bash
poetry run black .
```

### Continuous Integration

This project uses GitHub Actions for continuous integration. The following checks are performed on every push and pull request:

- Code formatting (Black)
- Type checking (MyPy)
- Linting (Flake8)
- Pre-commit hooks
- Unit tests
- Compatibility with Python 3.9-3.12

### Publishing

To publish a new version:

1. Update the version in `pyproject.toml`
2. Create a new release on GitHub
3. The GitHub Action will automatically build and publish to PyPI

Note: You'll need to set up a PyPI API token in your GitHub repository secrets as `PYPI_API_TOKEN`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate and ensure all checks pass before submitting your PR.

### Features to add
* collapse / expand all
* Reporting pages for task finished including start and finish dates
* Tidy code
* save layout "-c" to specify config file
* Add context support
* Update key bindings page removing unused
* Add column picker to command palette
* Autocomplete projects / tags
* Make current working task
* press h for help on commands / bindings
* create bug report for datatable and auto height
* Keep horizontal and vertical scroll on refresh
* Custom colors on age/active/due
* Clean up number for active
* Check if task command found

* Create proper readme
* Create github actions for build
* Create github issues / discussion
* Create contribution.md
* Create make file
