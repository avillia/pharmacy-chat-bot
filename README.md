# 🏥 Pharmacy SMS Chatbot

Interactive CLI chatbot for pharmacy conversations with OpenAI integration, template-based prompts, and automated follow-up actions.

## Features

- Phone number recognition and customer lookup
- Personalized greetings and AI-powered conversations  
- Lead information extraction and qualification
- Template-based messaging system
- Interactive CLI interface with [Typer](https://typer.tiangolo.com/) and Rich
- Mock email/callback follow-up actions

## Quick Start

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Set Environment Variables** (optional):
   ```bash
   # Create .env file (optional - defaults provided)
   OPENAI_API_KEY=your_openai_api_key_here
   PHARMACY_API_URL=https://67e14fb758cc6bf785254550.mockapi.io/pharmacies
   COMPANY_NAME=Pharmesol
   ```

3. **Use the Interactive CLI**:
   ```bash
   # Start interactive chat session
   uv run python main.py chat
   
   # Chat with a specific pharmacy number
   uv run python main.py chat --phone "+1-555-123-4567"
   
   # Show system information
   uv run python main.py info
   
   # See all available commands
   uv run python main.py --help
   ```

## CLI Commands

- **`chat`** - Interactive conversation with the chatbot
- **`demo`** - Run predefined scenarios to showcase capabilities
- **`test`** - Show available test commands

### Example Usage:
```bash
# Interactive chat as HealthFirst Pharmacy (known customer)
uv run python main.py chat --phone "+1-555-123-4567"

# Chat as new lead
uv run python main.py chat --phone "+1-555-NEW-LEAD"

# Run demo scenarios
uv run python main.py demo
```

## Testing

### Interactive Demo
```bash
# Complete demo flow with all scenarios
PYTHONPATH=. uv run pytest tests/test_demo_scenarios.py -k test_complete_demo_flow -v -s

# All demo scenarios
PYTHONPATH=. uv run pytest tests/test_demo_scenarios.py -v
```

### Test Suite
```bash
# Run all tests (40 tests total)
PYTHONPATH=. uv run pytest tests/ -v

# Specific test modules
PYTHONPATH=. uv run pytest tests/test_prompt_manager.py -v
PYTHONPATH=. uv run pytest tests/test_follow_up_actions.py -v
```

### Quick Tests
```bash
# Integration tests
PYTHONPATH=. uv run python tests/test_prompt_manager.py
PYTHONPATH=. uv run python tests/test_follow_up_actions.py
```

## Architecture

```
├── main.py                 # Interactive CLI application
├── env.py                  # Environment configuration
├── prompts/                # Template system
│   ├── responses/          # User-facing messages
│   ├── system/             # OpenAI system prompts & follow-up templates
│   └── extractions/        # Information extraction prompts
├── src/
│   ├── core/               # Business logic
│   └── api/                # External integrations
└── tests/                  # Comprehensive test suite
```

## Demo Scenarios

The system demonstrates three key scenarios:

1. **Returning Customer** (`+1-555-123-4567` - HealthFirst Pharmacy)
2. **Regular Customer** (`+1-555-666-7777` - MediCare Plus)  
3. **New Lead** (`+1-555-999-0000` - Unknown caller)

## API Integration

- **External API**: https://67e14fb758cc6bf785254550.mockapi.io/pharmacies
- **OpenAI**: GPT-3.5-turbo for conversations and information extraction
- **Mock Services**: Email sending, callback scheduling, CRM integration