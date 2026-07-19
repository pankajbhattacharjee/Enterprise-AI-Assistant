from pathlib import Path
from html import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def generate_report(path: Path, title: str, question: str, answer: str, findings: list[str]) -> None:
    styles = getSampleStyleSheet()
    safe_answer = escape(answer).replace("\n", "<br/>")
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1, 18), Paragraph("Executive Summary", styles["Heading2"]), Paragraph(safe_answer, styles["BodyText"]), Spacer(1, 12), Paragraph("Question", styles["Heading2"]), Paragraph(escape(question), styles["BodyText"])]
    if findings:
        story.extend([Spacer(1, 12), Paragraph("Key Findings & Recommendations", styles["Heading2"])])
        story.extend(Paragraph(f"&bull; {escape(finding)}", styles["BodyText"]) for finding in findings)
    SimpleDocTemplate(str(path), pagesize=letter, title=title).build(story)
