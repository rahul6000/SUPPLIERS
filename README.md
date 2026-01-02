# AI Supplier Agent

An intelligent agent for managing supplier relationships and procurement processes.

## Features

- Supplier data management
- Automated procurement workflows
- AI-powered supplier recommendations
- Performance analytics and reporting

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:
```bash
python src/main.py
```

## Project Structure

```
ai_supplier_agent/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── agents/
│   ├── models/
│   ├── services/
│   └── utils/
├── tests/
├── config/
├── docs/
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/ tests/
flake8 src/ tests/
```

## Configuration

Copy `.env.example` to `.env` and configure your environment variables.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License