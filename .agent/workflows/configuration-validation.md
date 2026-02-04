---
description: Catch configuration mismatches before runtime
---

### 1.1 Config Schema Validation
- [ ] Verify all config files exist
- [ ] Check required fields are present
- [ ] Validate data types (bool, int, str)
- [ ] Check for deprecated settings
- [ ] Validate paths point to existing files

### 1.2 Cross-File Consistency Check
- [ ] recruiter_messaging.py vs. run_bot.py imports
- [ ] secrets.py API keys format
- [ ] search.py vs. job requirements matching
- [ ] messaging_only_mode vs. user intent

### 1.3 Default Value Audit
- [ ] messaging_only_mode should default to False
- [ ] dry_run_mode should default to True for new setups
- [ ] AI features should default to disabled