from fpdf import FPDF
import io
import os

class InterviewReport(FPDF):
    def header(self):
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, "InterviewSim - Performance Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def generate_pdf(scores: dict, domain: str, difficulty: str) -> bytes:


    pdf = InterviewReport()

    # Add fonts FIRST
    font_path = os.path.join(os.path.dirname(__file__), "fonts")

    pdf.add_font("DejaVu", "", os.path.join(font_path, "DejaVuSans.ttf"), uni=True)
    pdf.add_font("DejaVu", "B", os.path.join(font_path, "DejaVuSans-Bold.ttf"), uni=True)
    pdf.add_font("DejaVu", "I", os.path.join(font_path, "DejaVuSans-Oblique.ttf"), uni=True)

    pdf.add_page()


    # pdf = InterviewReport()

    # pdf.add_font("DejaVu", "I", "/Library/Fonts/DejaVuSans-Oblique.ttf", uni=True)
    # pdf.add_font("DejaVu", "", "/Library/Fonts/DejaVuSans.ttf", uni=True)
    # pdf.add_font("DejaVu", "B", "/Library/Fonts/DejaVuSans-Bold.ttf", uni=True)

    # pdf.set_auto_page_break(auto=True, margin=15)

    # pdf.add_page()

    # ── Meta ──
    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Domain: {domain}   |   Difficulty: {difficulty}   |   Hire Signal: {scores.get('hire_signal','').upper()}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Overall score ──
    pdf.set_font("DejaVu", "B", 28)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 14, f"Overall Score: {scores.get('overall', 0)} / 10", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Rubric scores ──
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Rubric Breakdown", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    for dim, score in scores.get("scores", {}).items():
        pdf.set_text_color(80, 80, 80)
        pdf.cell(80, 7, dim)
        # Draw bar
        bar_x = pdf.get_x()
        bar_y = pdf.get_y() + 1
        pdf.set_fill_color(220, 220, 220)
        pdf.rect(bar_x, bar_y, 80, 5, "F")
        fill_w = (score / 10) * 80
        pdf.set_fill_color(127, 119, 221)
        pdf.rect(bar_x, bar_y, fill_w, 5, "F")
        pdf.set_text_color(80, 80, 80)
        pdf.cell(85, 7, "")
        pdf.cell(0, 7, f"{score}/10", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Per question ──
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Question Breakdown", new_x="LMARGIN", new_y="NEXT")
    for i, q in enumerate(scores.get("per_question", []), 1):
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(50, 50, 50)
        question_text = f"Q{i}: {q.get('question', '')[:100]}"
        pdf.multi_cell(0, 6, question_text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 5, f"Score: {q.get('score','?')}/10  |  {q.get('summary','')}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(30, 130, 80)
        pdf.multi_cell(0, 5, f"+ {q.get('strength','')}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(180, 100, 20)
        pdf.multi_cell(0, 5, f"- {q.get('weakness','')}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # ── Strengths & gaps ──
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Strengths", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    for s in scores.get("top_strengths", []):
        pdf.set_text_color(30, 130, 80)
        pdf.multi_cell(0, 6, f"✓  {s}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Gaps to Fix", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    for g in scores.get("top_gaps", []):
        pdf.set_text_color(180, 100, 20)
        pdf.multi_cell(0, 6, f"•  {g}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Study Plan", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 6, scores.get("improvement_plan", ""), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())