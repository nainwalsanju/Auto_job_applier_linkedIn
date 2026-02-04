---
description: Test full flows from end-to-end
---

### 3.1 Happy Path: Search → Apply → Message
- [ ] Bot logs in to LinkedIn successfully
- [ ] Search filters apply correctly
- [ ] Job listings load and iterate
- [ ] Job details page opens
- [ ] Recruiter detection finds hiring team
- [ ] Message button click opens overlay
- [ ] Message text populates correctly
- [ ] Send button click succeeds
- [ ] Modal closes after send
- [ ] Job application completes (if not messaging_only_mode)
- [ ] CSV records all actions correctly

### 3.2 Unhappy Paths
- [ ] No recruiters present → skip gracefully
- [ ] Only InMail available → skip with correct reason
- [ ] Daily limit reached → stop messaging, continue searching
- [ ] Message button missing → skip without crash
- [ ] Overlay bubble doesn't open → timeout and retry
- [ ] Send button not found → clean error message
- [ ] ChromeDriver disconnects → handle gracefully
- [ ] Network timeout → retry with backoff

### 3.3 Edge Cases
- [ ] Multiple recruiters on same job
  - [ ] Messages each once
  - [ ] Respects daily limit
  - [ ] Tracks recruiter IDs correctly
- [ ] Same recruiter on different jobs
  - [ ] Skips after first message
  - [ ] Records skip reason correctly
- [ ] recruiter with no name/title
  - [ ] Uses placeholders gracefully
  - [ ] Doesn't crash on missing data
- [ ] LinkedIn UI change (new overlay system)
  - [ ] Detects new UI pattern
  - [ ] Logs warning for manual review
  - [ ] Continues with fallback selectors