# Contributing to AI Novelist

Thank you for your interest in contributing to AI Novelist! This document provides guidelines for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all contributors to create a welcoming and inclusive environment.

## Getting Started

### Reporting Bugs

Found a bug? Please help us by creating an issue:

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** with a clear title
3. **Describe the problem** in detail:
   - What you expected to happen
   - What actually happened
   - Steps to reproduce
   - Environment details (OS, Python/Node versions)
   - Screenshots if relevant
4. **Add labels** if you have permission, or we'll add them

### Suggesting Features

Have an idea to improve AI Novelist?

1. **Check existing features** first
2. **Create a feature request** issue
3. **Explain the value** - how does this help users?
4. **Provide context** - use cases, examples, mockups if possible
5. **Discuss before coding** - let's align on approach first

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/ZhaoDezhang9/ai-novelist.git
cd ai-novelist

# Backend setup
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Configuration
cp .env.example .env
# Edit .env with your API keys
```

### Running Locally

```bash
# Start both backend and frontend (Windows)
./启动.bat

# Manual startup
# Terminal 1 (backend):
python -m uvicorn main:app --reload --port 8000

# Terminal 2 (frontend):
cd frontend
npm run dev
```

Visit http://localhost:3000

## Project Structure

```
ai-novelist/
├── backend/           # FastAPI application
│   ├── main.py       # Entry point
│   ├── models/       # SQLAlchemy models
│   ├── routes/       # API endpoints
│   ├── services/     # Business logic
│   └── utils/        # Utilities
├── frontend/         # React application
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/     # Page components
│   │   ├── hooks/     # Custom React hooks
│   │   └── styles/    # CSS/SCSS files
│   └── package.json
├── tests/            # Test files
└── docs/             # Documentation
```

## Code Style

### Python
- Follow [PEP 8](https://pep8.org/)
- Use type hints where helpful
- Maximum line length: 88 (Black default)
- Use Black for formatting: `black .`
- Use isort for imports: `isort .`

### TypeScript/React
- Use project tsconfig settings
- Prefer functional components with hooks
- Use TypeScript strict mode
- Use ESLint and Prettier: `npm run lint`
- Use meaningful variable names

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add dark mode toggle
fix: resolve memory leak in tiered memory
docs: update contributing guide
chore: update dependencies
test: add unit tests for outline engine
refactor: simplify quality gate logic
```

Examples:
- `feat: add character relationship graph`
- `fix: handle API key validation errors`
- `docs: improve installation instructions`

## Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_quality_gates.py

# With coverage
pytest --cov=backend tests/
```

### Frontend Tests
```bash
cd frontend
# Type checking
npm run type-check

# Run tests
npm test
```

### Before Submitting
- All tests pass: `pytest && cd frontend && npm test`
- TypeScript compiles: `cd frontend && npx tsc --noEmit`
- Code is formatted: `black . && cd frontend && npm run format`

## Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feat/your-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Ensure code quality** (formatting, linting)
7. **Commit with clear messages**
8. **Push to your fork**
9. **Create a Pull Request**

### PR Requirements
- **Title**: Clear, descriptive (feat/fix/docs/etc.)
- **Description**: What changes, why, how to test
- **Linked issues**: Reference related issues with `#123`
- **Passing CI**: All checks must pass
- **Review ready**: Code is complete and tested

### Review Process
1. Maintainers will review within a few days
2. Address review comments with additional commits
3. Once approved, maintainers will merge
4. Your contribution will be part of the next release!

## Getting Help

- **Documentation**: Check the [README.md](README.md)
- **Issues**: Search existing issues or create new
- **Discussion**: GitHub Discussions (coming soon)
- **Contact**: Open a GitHub issue for questions

## Recognition

All contributors are acknowledged in:
- GitHub contributors list
- Release notes
- Project documentation (when significant)

Thank you for making AI Novelist better! 🚀