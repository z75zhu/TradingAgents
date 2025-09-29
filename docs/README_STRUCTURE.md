# TradingAgents Repository Structure

## Directory Organization

### `/tests/`
Organized test suite with clear categorization:

- **`unit/`** - Individual component tests
  - `test_dynamic_model_selection.py` - Model selection logic
  - `test_finnhub_connection.py` - Finnhub API connectivity

- **`integration/`** - Multi-component integration tests
  - `test_agent_live_data.py` - Agent data integration
  - `test_enhanced_finnhub.py` - Enhanced Finnhub features

- **`system/`** - Full system comprehensive tests
  - `test_bedrock_implementations.py` - Complete Bedrock integration
  - `test_env_config.py` - Environment configuration system

### `/docs/`
Project documentation:
- `CLAUDE.md` - Claude Code integration guide
- `LIVE_DATA_SETUP.md` - Live data integration setup
- `README_STRUCTURE.md` - This file

### `/scripts/`
Utility scripts:
- `run_tests.py` - Comprehensive test runner
- `check_bedrock_models.py` - Bedrock model availability checker

## Running Tests

### Quick Start
```bash
# Run all tests in proper order
python scripts/run_tests.py

# Run specific category
python scripts/run_tests.py --category unit
python scripts/run_tests.py --category integration
python scripts/run_tests.py --category system

# List available tests
python scripts/run_tests.py --list
```

### Test Categories

1. **Unit Tests** - Fast, isolated component tests
2. **Integration Tests** - Multi-component interaction tests
3. **System Tests** - Full system comprehensive validation

### Environment Setup
Ensure your `.env` file is configured before running tests:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Benefits of This Structure

- **🔒 Security**: No API keys in version control
- **📁 Organization**: Clear separation of concerns
- **🧪 Testing**: Proper test categorization and execution
- **📚 Documentation**: Centralized knowledge base
- **⚡ Performance**: Run only relevant test categories
- **👥 Collaboration**: Easy for team members to understand structure