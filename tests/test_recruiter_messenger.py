import re

from modules import recruiter_messenger


def test_trim_to_limit_basic():
    assert recruiter_messenger._trim_to_limit("hello", 10) == "hello"
    assert recruiter_messenger._trim_to_limit("hello", 5) == "hello"
    assert recruiter_messenger._trim_to_limit("hello", 4) == "h..."
    assert recruiter_messenger._trim_to_limit("hello", 0) == ""


def test_generate_connection_note_respects_limit():
    recruiter_info = {"name": "Alex Johnson"}
    note = recruiter_messenger.generate_connection_note(
        aiClient=None,
        recruiter_info=recruiter_info,
        job_description="Backend role working on Java microservices.",
        job_title="Senior Backend Engineer",
        company_name="ExampleCo",
    )
    assert len(note) <= recruiter_messenger.connection_note_max_chars
    assert "Alex" in note
    assert re.search(r"\s{2,}", note) is None


def test_generate_personalized_message_trims_body():
    recruiter_info = {"name": "Sam Recruiter"}
    subject, body = recruiter_messenger.generate_personalized_message(
        aiClient=None,
        recruiter_info=recruiter_info,
        job_description="A" * 3000,
        job_title="Backend Engineer",
        company_name="ExampleCo",
        job_link="https://example.com/job",
    )
    assert len(subject) <= 200
    assert len(body) <= 1900
    assert "Sam" in body
