---
description: Ensure all failures are recoverable and logged
---

### 7.1 Exception Coverage
Test each exception path:
- [ ] NoSuchElementException → logged, returns False
- [ ] TimeoutException → logged, retries 3x
- [ ] ElementClickInterceptedException → scrolls and retries
- [ ] WebDriverException → cleanup attempted, returns error
- [ ] AttributeError → logs stack trace, returns safe value
- [ ] KeyError in CSV → uses default, continues

### 7.2 Recovery Testing
Force each failure scenario:
- [ ] Lost network connection → reconnect, retry
- [ ] LinkedIn session expired → re-login prompt
- [ ] ChromeDriver crash → respawn driver, continue
- [ ] LinkedIn captcha → prompt for manual solve, resume
- [ ] Rate limit reached → wait 15min, resume
- [ ] Browser window closed → reopen, restore state

### 7.3 Log Quality Testing
- [ ] All operations have debug logging
- [ ] Errors include stack traces
- [ ] Timing data logged for performance analysis
- [ ] HTML dumps saved when unexpected UI encountered
- [ ] Logs rotate at reasonable size (<100MB)
- [ ] Sensitive data (passwords, API keys) excluded from logs