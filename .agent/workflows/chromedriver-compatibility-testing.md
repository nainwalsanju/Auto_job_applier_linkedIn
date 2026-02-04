---
description: Ensure browser/driver stability
---

### 4.1 Version Matrix Testing
Test Matrix:
| Chrome Version | ChromeDriver Version | Result | Notes |
|--------------|-------------------|--------|-------|
| 131          | 131              | [ ]    | Stable baseline |
| 132          | 132              | [ ]    | Test new UI changes |
| 130          | 130              | [ ]    | Test backward compat |
| Latest        | Latest            | [ ]    | Test bleeding edge |

### 4.2 Platform Testing
- [ ] macOS Ventura (your current)
- [ ] macOS Sonoma
- [ ] macOS Sequoia
- [ ] Linux (Ubuntu 22.04)
- [ ] Linux (Ubuntu 24.04)
- [ ] Windows 11
- [ ] Windows 10

### 4.3 Browser Options Testing
Test configurations:
```python
# Config A: Basic (current)
chrome_options.add_argument("--start-maximized")

# Config B: Anti-detection
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

# Config C: Headless
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")

# Config D: User Profile
chrome_options.add_argument(f"user-data-dir={profile_path}")
chrome_options.add_argument(f"profile-directory={profile_name}")

# Config E: Debugging
chrome_options.add_argument("--enable-logging")
chrome_options.add_argument("--log-level=0")



4.4 Stress Testing

 100+ rapid element interactions
 50+ consecutive message sends
 10+ modal open/close cycles
 Memory leak detection (Chrome process size over time)
 Zombie process detection (orphaned chromedrivers)

**Would have caught**: ChromeDriver version incompatibility, memory leaks causing crashes

---

## **Workflow 5: Dry-Run & Safety Testing** 🛡️
**Purpose**: Validate behavior without real side effects

```markdown
### 5.1 Dry-Run Mode Testing
- [ ] dry_run_mode = True doesn't actually send messages
- [ ] All find_recruiters() logic executes
- [ ] All generate_personalized_message() logic executes
- [ ] send_message_to_recruiter() returns success without sending
- [ ] CSV records "Dry run" status correctly
- [ ] No LinkedIn API calls made

### 5.2 Safety Checks
- [ ] Confirm before sending first real message
  - [ ] User prompt: "About to send message to {recruiter}"
  - [ ] Displays full message content
  - [ ] Shows recruiter/job details
  - [ ] Requires typing "CONFIRM" to proceed
- [ ] Daily limit warning before reaching
  - [ ] Warning at 80% of limit
  - [ ] Warning at 95% of limit
  - [ ] Stop at 100% with clear message
- [ ] InMail preservation check
  - [ ] Counts InMail skips separately
  - [ ] Reports summary: "X free messages sent, Y InMail skipped"

### 5.3 Rollback Testing
- [ ] Delete message from LinkedIn inbox after dry run
- [ ] Edit message content in config → regenerate
- [ ] Change recruiter in CSV → respects new data
- [ ] Clear CSV completely → starts fresh