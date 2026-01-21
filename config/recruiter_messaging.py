'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    26.01.18.22.50

Contributor: Sanjay Nainwal (sanjaynainwal129@gmail.com) - Feature: Recruiter Messaging
'''


###################################################### RECRUITER MESSAGING CONFIGURATION ######################################################


# Enable recruiter messaging feature
enable_recruiter_messaging = True          # True or False, Note: True or False are case-sensitive


# \u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e Message Sending Preferences \u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c

# Maximum messages to send per day (no InMail cost, so can send more)
max_messages_per_day = 50              # Only Non Negative Integers Eg: 10, 20, 50, 100

# Delay between messages in seconds (to avoid spam detection)
message_delay_seconds = 30             # Only Non Negative Integers Eg: 15, 30, 45, 60

# Skip messaging if already applied to job via Easy Apply?
skip_if_already_applied = False         # True or False, Note: True or False are case-sensitive

# Messaging Only Mode - Skip Easy Apply and only message recruiters?
messaging_only_mode = True            # True or False, Note: True or False are case-sensitive
'''
Set to True if you want to ONLY message recruiters without applying via Easy Apply.
This is useful when you want to focus on direct recruiter outreach.
Note: When True, the bot will:
- Search for jobs
- Message recruiters (if they accept free messages)
- Skip all Easy Apply applications
'''



# \u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e InMail Preservation (CRITICAL) \u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c

# Only message recruiters who accept free messages from anyone (preserves InMail credits)
only_free_messages = True              # True or False, Note: True or False are case-sensitive

# Skip recruiters who require InMail (preserves your LinkedIn Premium InMail credits)
skip_inmail_required = True            # True or False, Note: True or False are case-sensitive


# \u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e Message Templates \u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c

# Multiple message templates for A/B testing (each with subject and body)
message_templates = [
    {
        "name": "professional_formal",
        "subject": "Interest in {job_title} Position at {company_name}",
        "body": """Dear {recruiter_name},

I am writing to express my strong interest in the {job_title} position at {company_name} that I recently discovered.

{personalized_intro}

With {years_of_experience} years of experience in backend development, I believe I would be a valuable addition to your team. My expertise includes Java, Spring Boot, and scalable distributed systems.

{why_interested}

I would welcome the opportunity to discuss how my background aligns with your requirements. Please find my contact information below:

Resume: https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing
LinkedIn: https://www.linkedin.com/in/sanjay-nainwal/
Portfolio: https://sanjaynainwal.vercel.app/
Phone: +91 9720423975

Job Listing: {job_link}

Thank you for your time and consideration.

Best regards,
{your_name}"""
    },
    {
        "name": "enthusiastic_casual",
        "subject": "Excited About {job_title} at {company_name}!",
        "body": """Hi {recruiter_name},

I just came across the {job_title} opening at {company_name} and I'm really excited about the opportunity!

{personalized_intro}

I've been working in backend development for {years_of_experience} years now, and I think I'd be a great fit for this role. I've got solid experience with Java, Spring Boot, and building distributed systems at scale.

{why_interested}

I'd love to chat about how I can contribute to your team! Here are my details:

Resume: https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing
LinkedIn: https://www.linkedin.com/in/sanjay-nainwal/
Portfolio: https://sanjaynainwal.vercel.app/
Phone: +91 9720423975

Job Listing: {job_link}

Looking forward to hearing from you!

Best,
{your_name}"""
    },
    {
        "name": "concise_direct",
        "subject": "Application for {job_title} at {company_name}",
        "body": """Hello {recruiter_name},

I'm interested in the {job_title} position at {company_name}.

{personalized_intro}

With {years_of_experience} years in backend development, I specialize in Java, Spring Boot, and distributed systems.

{why_interested}

Let's discuss my fit for this role:

Resume: https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing
LinkedIn: https://www.linkedin.com/in/sanjay-nainwal/
Portfolio: https://sanjaynainwal.vercel.app/
Phone: +91 9720423975

Job Link: {job_link}

Best regards,
{your_name}"""
    },
    {
        "name": "value_focused",
        "subject": "Bringing {years_of_experience} Years Experience to {job_title} at {company_name}",
        "body": """Hi {recruiter_name},

I'm excited about the {job_title} opportunity at {company_name} and believe my {years_of_experience} years of backend development experience would add significant value to your team.

{personalized_intro}

My expertise in Java, Spring Boot, and scalable distributed systems aligns perfectly with the requirements of this role.

{why_interested}

I'd be happy to discuss how my background can contribute to your company's success. My contact details:

Resume: https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing
LinkedIn: https://www.linkedin.com/in/sanjay-nainwal/
Portfolio: https://sanjaynainwal.vercel.app/
Phone: +91 9720423975

Job Listing: {job_link}

Looking forward to connecting!

Best,
{your_name}"""
    },
    {
        "name": "story_driven",
        "subject": "My Journey Aligns with {company_name}'s {job_title} Vision",
        "body": """Hello {recruiter_name},

After reviewing the {job_title} position at {company_name}, I'm impressed by your team's approach and believe my professional journey aligns perfectly with this opportunity.

{personalized_intro}

Over my {years_of_experience} years in backend development, I've built expertise in Java, Spring Boot, and distributed systems while delivering solutions at scale.

{why_interested}

I'm particularly drawn to {company_name} because [company values/mission aligns with my experience]. I'd love to share my story and discuss how I can contribute.

Contact Information:
Resume: https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing
LinkedIn: https://www.linkedin.com/in/sanjay-nainwal/
Portfolio: https://sanjaynainwal.vercel.app/
Phone: +91 9720423975

Job Link: {job_link}

Thank you for considering my application.

Warm regards,
{your_name}"""
    },
    {
        "name": "question_based",
        "subject": "Question About {job_title} at {company_name}",
        "body": """Hi {recruiter_name},

I'm very interested in the {job_title} position at {company_name} and have a question about the role.

{personalized_intro}

With {years_of_experience} years of backend development experience, including extensive work with Java, Spring Boot, and distributed systems, I'm wondering about the team's current tech stack and challenges.

{why_interested}

I'd love to learn more about the position and discuss how my background might fit. Here are my details:

Resume: https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing
LinkedIn: https://www.linkedin.com/in/sanjay-nainwal/
Portfolio: https://sanjaynainwal.vercel.app/
Phone: +91 9720423975

Job Listing: {job_link}

Would you be open to a brief conversation?

Best regards,
{your_name}"""
    }
]

# Legacy single template variables (for backward compatibility - DEPRECATED, use message_templates instead)
message_subject = "Interested in {job_title} position at {company_name}"
message_template = """Hello {recruiter_name},

I came across the {job_title} position at {company_name} and I'm very interested in this opportunity.

{personalized_intro}

With {years_of_experience} years of experience in backend development, I believe I would be a strong fit for this role. I've worked extensively with Java, Spring Boot, and distributed systems at scale.

{why_interested}

I would love to discuss how my background aligns with your needs. Here are my details:

Resume: https://drive.google.com/file/d/1kLdZWzTeRAAm4QtWrv2UQjHJ-H5ADOgd/view?usp=sharing
LinkedIn: https://www.linkedin.com/in/sanjay-nainwal/
Portfolio: https://sanjaynainwal.vercel.app/
Phone: +91 9720423975

Job Listing: {job_link}

Best regards,
{your_name}
"""

'''
Available template variables:
- {recruiter_name}: Recruiter's first name or full name
- {job_title}: Title of the job posting
- {company_name}: Company name
- {job_link}: Direct link to the job posting
- {your_name}: Your name from personals.py
- {years_of_experience}: Your experience from questions.py
- {personalized_intro}: AI-generated personalized introduction (if AI enabled)
- {why_interested}: AI-generated reason for interest (if AI enabled)
- {key_skills}: Your relevant skills from profile
'''


# \u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e AI-Powered Personalization \u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c

# Use AI to personalize messages based on job description?
use_ai_for_messages = False             # True or False, Note: True or False are case-sensitive

# Level of AI personalization
ai_personalization_level = "high"      # "low", "medium", "high"
'''
- "low": Basic job title and company name insertion
- "medium": Add relevant skills matching from job description
- "high": Full personalization with job-specific intro and interest explanation
'''


# \u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e Message History Tracking \u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c

# File to track all sent messages (prevents duplicates)
message_history_file = "all excels/recruiter_messages_history.csv"


# \u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e\u003e Testing and Safety \u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c\u003c

# Dry run mode - generate messages but don't actually send them (for testing)
dry_run_mode = False                   # True or False, Note: True or False are case-sensitive




############################################################################################################
'''
THANK YOU for using this tool 😊! Wishing you the best in your job hunt 🙌🏻!

Sharing is caring! If you found this tool helpful, please share it with your peers 🥺. Your support keeps this project alive.

As an independent developer, I pour my heart and soul into creating tools like this, driven by the genuine desire to make a positive impact.

Your support, whether through donations big or small or simply spreading the word, means the world to me and helps keep this project alive and thriving.

Gratefully yours 🙏🏻,
Sai Vignesh Golla
'''
############################################################################################################
