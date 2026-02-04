---
description: Catch when fixes break existing functionality
---

### 10.1 Smoke Tests
Run before any commit:
- [ ] Basic job search works
- [ ] Easy Apply completes (if enabled)
- [ ] Recruiter messaging works (if enabled)
- [ ] CSV files are written
- [ ] Bot exits cleanly

### 10.2 Integration Tests
- [ ] Recruiter messaging doesn't break Easy Apply
- [ ] Easy Apply doesn't break recruiter messaging
- [ ] AI features don't break non-AI mode
- [ ] Multiple search terms work correctly
- [ ] Pagination works after applying

### 10.3 Backwards Compatibility
- [ ] Old config files still work
- [ ] Old job histories import correctly
- [ ] Legacy recruiter formats handled
- [ ] Existing login sessions respected