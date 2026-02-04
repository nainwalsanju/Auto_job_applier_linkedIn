---
description: Test individual components in isolation
---

### 2.1 Recruiter Messenger Module
Test: modules/recruiter_messenger.py
- [ ] find_recruiters_on_job_page() 
  - [ ] Returns empty list when no recruiters present
  - [ ] Detects both hiring_team and connections sections
  - [ ] Correctly parses recruiter names, titles, IDs
  - [ ] Accurately detects can_message and is_free_message flags
  
- [ ] check_message_capability()
  - [ ] Correctly identifies InMail vs free messages
  - [ ] Handles connection degree parsing (1st/2nd/3rd)
  - [ ] Falls back gracefully when degree not found
  
- [ ] generate_personalized_message()
  - [ ] Formats template variables correctly
  - [ ] Inserts AI personalization when enabled
  - [ ] Falls back to template when AI disabled
  - [ ] Respects LinkedIn character limits (200 subject, 1900 body)
  
- [ ] should_skip_recruiter()
  - [ ] Skips already messaged recruiters
  - [ ] Skips InMail when skip_inmail_required = True
  - [ ] Respects daily message limit
  - [ ] Returns appropriate skip reasons

### 2.2 Modal Management
- [ ] _ensure_modal_closed()
  - [ ] Closes all open messaging bubbles
  - [ ] Handles "discard draft" confirmations
  - [ ] Uses multiple close selector fallbacks
  - [ ] JavaScript fallback executes correctly
  - [ ] No exception on already-clean state

### 2.3 Message Field Interaction
- [ ] find_message_body_field()
  - [ ] Locates contenteditable div in active bubble
  - [ ] Waits for element visibility
  - [ ] Handles multiple selector variants
  - [ ] Doesn't timeout on slow rendering
  
- [ ] insert_message_text()
  - [ ] JavaScript insertion works
  - [ ] send_keys fallback works
  - [ ] Triggers input/change events
  - [ ] Verifies text was actually inserted