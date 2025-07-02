# Environment Configuration Setup

This document explains how to configure environment variables for the Chat Frontend application.

## Quick Start

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your actual values
3. **Never commit `.env`** to version control

## Environment Variables

### API Keys (Future Use)

The application supports multiple API services. Add the keys you need:

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Custom API Key
CHAT_API_KEY=your_custom_api_key_here
```

### Backend Configuration (Optional)

Override default backend connection settings:

```bash
# Backend server connection
CHAT_BACKEND_HOST=192.168.1.223  # Default: 192.168.1.223
CHAT_BACKEND_PORT=8000           # Default: 8000
CHAT_BACKEND_SSL=false           # Default: false
```

### UI Configuration (Optional)

Customize application appearance:

```bash
# Theme preference
CHAT_THEME_MODE=light            # Options: light, dark, system
```

## Configuration Validation

The application includes built-in environment validation:

```python
from src.config import validate_environment

# Check environment configuration
result = validate_environment()
print(f"Status: {result['status']}")
print(f"Issues: {result['issues']}")
print(f"Recommendations: {result['recommendations']}")
```

## API Key Management

### Loading API Keys

```python
from src.config import get_api_key_config

api_config = get_api_key_config()

# Check if a key is configured
if api_config.has_api_key("openai"):
    key = api_config.get_api_key("openai")
    # Use the key...

# Get all configured services
services = api_config.get_configured_services()
print(f"Configured services: {services}")
```

### Validating Required Keys

```python
# Validate that specific keys are present (fail-fast)
try:
    api_config.validate_required_keys(["openai", "anthropic"])
    print("All required keys are present")
except ValueError as e:
    print(f"Missing keys: {e}")
```

## Security Best Practices

1. **Never commit `.env`** - it's in `.gitignore` for a reason
2. **Never log API keys** - the config system only logs presence/absence
3. **Use environment variables** in production deployments
4. **Rotate keys regularly** and update `.env` as needed

## Troubleshooting

### Missing Keys
- Check that `.env` file exists and has correct variable names
- Verify no extra spaces around `=` in variable assignments
- Ensure file permissions allow reading

### Invalid Configuration
- Run `validate_environment()` to check for issues
- Check logs for specific error messages
- Verify data types (booleans should be "true"/"false")

### Development vs Production
- Use `.env` file for local development
- Use actual environment variables in production
- Never ship `.env` files with applications
