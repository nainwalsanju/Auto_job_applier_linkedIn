# Migration Guide - Security Refactoring

## What Changed

### Phase 1: Security Hardening (Completed)

**Before:** Credentials were hardcoded in `config/secrets.py`
```python
username = "sanjaynainwal129@gmail.com"
password = "B@NGB@ng12"
llm_api_key = "sk-c101c45ee7af44c19e77e9ff43f59bd9"
```

**After:** Credentials are loaded from environment variables or `.env` file
```python
# No hardcoded credentials!
# Load from environment variables or .env file
```

## Migration Steps

### 1. Create Your `.env` File

Copy the example file and fill in your values:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_secure_password
LLM_API_KEY=your-api-key
```

### 2. Install New Dependencies

```bash
pip install python-dotenv pydantic pydantic-settings
```

### 3. Remove Old Credentials (Optional but Recommended)

The old credentials in `config/secrets.py` are now ignored. You can:
- Keep them as fallback (not recommended)
- Comment them out for security
- Delete them entirely

### 4. Test the Configuration

```bash
python config/secure_config.py
```

Should output:
```
LinkedIn Configuration:
  Username: ***
  Password: ***
AI Configuration:
  Use AI: False
  Provider: deepseek
  Configured: True
```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `LINKEDIN_USERNAME` | LinkedIn email | No* |
| `LINKEDIN_PASSWORD` | LinkedIn password | No* |
| `USE_AI` | Enable AI features (true/false) | No |
| `AI_PROVIDER` | openai, deepseek, or gemini | No |
| `LLM_API_URL` | API endpoint URL | No |
| `LLM_API_KEY` | API key | If AI enabled |
| `LLM_MODEL` | Model name | No |
| `LLM_SPEC` | API specification | No |
| `STREAM_OUTPUT` | Stream AI output | No |

*Required only if you want auto-login

## Backward Compatibility

The old variables in `config/secrets.py` still work but are deprecated:
```python
# Old way (still works but deprecated)
from config.secrets import username, password, llm_api_key

# New way (recommended)
from config.secure_config import get_linkedin_credentials, get_llm_api_key
username, password = get_linkedin_credentials()
api_key = get_llm_api_key()
```

## Security Best Practices

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Use strong passwords** - Don't reuse passwords
3. **Rotate API keys** - If a key is compromised, regenerate it
4. **Use least privilege** - Only grant necessary permissions to API keys

## Troubleshooting

### "AI is not enabled" error
Set `USE_AI=true` in your `.env` file

### "API key not found" error
Make sure `LLM_API_KEY` is set in your `.env` file

### Configuration not loading
Make sure `.env` file is in the project root directory

## Next Steps

- [ ] Complete Phase 2: Code Architecture
- [ ] Complete Phase 3: Error Handling & Logging
- [ ] Complete Phase 4: Code Quality
- [ ] Complete Phase 5: Testing

---

**Document Version:** 1.0
**Last Updated:** January 15, 2026
