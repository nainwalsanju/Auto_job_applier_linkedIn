"""
Author:     Sanjay Nainwal
GitHub:     https://github.com/nainwalsanju/Auto_job_applier_linkedIn
Description: Module for tailoring resumes and generating custom PDFs.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from modules.helpers import print_lg, make_directories


def generate_tailored_pdf(
    content: str,
    job_title: str,
    company_name: str,
    output_dir: str = "data/resumes/tailored",
) -> str:
    """
    Generates a clean PDF containing the tailored cover letter/summary.
    Returns the path to the generated file.
    """
    try:
        make_directories([output_dir])

        # Create unique filename
        safe_company = "".join(x for x in company_name if x.isalnum())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Resume_{safe_company}_{timestamp}.pdf"
        file_path = os.path.join(output_dir, filename)

        # Setup PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Justify", alignment=TA_JUSTIFY))

        story = []

        # Header (Job Title)
        header_text = f"<b>Application for {job_title} at {company_name}</b>"
        story.append(Paragraph(header_text, styles["Heading2"]))
        story.append(Spacer(1, 12))

        # Date
        date_text = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(date_text, styles["Normal"]))
        story.append(Spacer(1, 24))

        # Tailored Content
        # Split by double newlines to handle paragraphs
        paragraphs = content.split("\n\n")
        for p in paragraphs:
            if p.strip():
                story.append(
                    Paragraph(p.strip().replace("\n", "<br/>"), styles["Justify"])
                )
                story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        print_lg(f"✅ Tailored PDF generated: {file_path}")
        return os.path.abspath(file_path)

    except Exception as e:
        print_lg(f"❌ Error generating tailored PDF: {e}")
        return ""


def get_candidate_base_info() -> str:
    """Collects base candidate info from personals and questions config."""
    try:
        from config.personals import first_name, last_name, current_city
        from config.questions import years_of_experience

        info = (
            f"Name: {first_name} {last_name}\n"
            f"Location: {current_city}\n"
            f"Experience: {years_of_experience} years\n"
            f"Primary Stack: Java, Spring Boot, Backend Systems\n"
        )
        return info
    except Exception:
        return "Generic Backend Developer with Java/Python experience."
