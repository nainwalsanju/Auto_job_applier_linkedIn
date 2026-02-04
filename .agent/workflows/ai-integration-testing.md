---
description: Test AI features safely
---

## 6.1 AI Provider Testing
Test this provider:
- [ ] DeepSeek (if configured)
  - [ ] API key valid
  - [ ] Cost calculation tracking
  - [ ] Timeout handling

### 6.2 AI Fallback Testing
- [ ] AI fails → uses template
- [ ] AI timeout → uses cached response
- [ ] AI returns empty → uses default text
- [ ] AI error logged clearly → continues without crash
- [ ] Network error → retries with exponential backoff

### 6.3 Message Quality Testing
- [ ] AI-generated messages include recruiter name
- [ ] AI-generated messages include job title
- [ ] AI-generated messages are under character limit
- [ ] AI-generated messages don't have artifacts
- [ ] AI-generated messages sound professional