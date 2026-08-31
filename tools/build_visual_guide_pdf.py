from __future__ import annotations

from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "docs" / "images"
TMP_DIR = ROOT / "tmp" / "pdfs"
OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT = OUTPUT_DIR / "AEGIS-Web-Continuation-Visual-Guide.pdf"


FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
NOTO_DIR = Path("/opt/codex/runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/share/fonts/truetype")
pdfmetrics.registerFont(TTFont("NotoSans", str(NOTO_DIR / "NotoSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(NOTO_DIR / "NotoSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSansMono", str(FONT_DIR / "DejaVuSansMono.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSansMono-Bold", str(FONT_DIR / "DejaVuSansMono-Bold.ttf")))


def pil_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, size: int, fill: str, bold: bool = False) -> None:
    font = pil_font(size, bold)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    width, height = right - left, bottom - top
    x = box[0] + (box[2] - box[0] - width) / 2
    y = box[1] + (box[3] - box[1] - height) / 2 - top
    draw.text((x, y), text, font=font, fill=fill)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: str) -> None:
    draw.line([start, end], fill=fill, width=7)
    draw.polygon([(end[0], end[1]), (end[0] - 16, end[1] - 10), (end[0] - 16, end[1] + 10)], fill=fill)


def diagram_png(stem: str, output: Path) -> None:
    image = PILImage.new("RGB", (1500, 844), "#07111f")
    draw = ImageDraw.Draw(image)
    title_font = pil_font(46, True)
    sub_font = pil_font(27)

    titles = {
        "01-system-overview": ("AEGIS Web Continuation - System Overview", "Workflow guidance stays separate from repository execution."),
        "02-install-flow": ("Windows Installation Flow", "Preview first. Apply only after paths and conflicts are reviewed."),
        "03-mobile-handoff": ("Safe Handoff from PC to Phone", "Push a verifiable checkpoint before leaving the local machine."),
        "04-cli-fallback": ("When Codex CLI Cannot Continue", "The Skill preserves workflow state; it does not bypass usage limits."),
    }
    title, subtitle = titles[stem]
    draw.text((75, 58), title, font=title_font, fill="#f8fafc")
    draw.text((75, 122), subtitle, font=sub_font, fill="#94a3b8")

    if stem == "01-system-overview":
        cards = [
            ((80, 275, 350, 475), "Phone / Web", "Chat or Work", "#172554", "#60a5fa"),
            ((430, 275, 700, 475), "AEGIS Skill", "Identity - Scope - Evidence", "#052e2b", "#2dd4bf"),
            ((780, 275, 1050, 475), "Codex Cloud", "Inspect - Edit - Build - Test", "#3b1d0b", "#fb923c"),
            ((1130, 275, 1420, 475), "GitHub", "Branch - Commit - PR", "#1e293b", "#cbd5e1"),
        ]
        for index, (box, head, line, bg, stroke) in enumerate(cards):
            draw.rounded_rectangle(box, radius=28, fill=bg, outline=stroke, width=4)
            centered(draw, (box[0], box[1] + 30, box[2], box[1] + 105), head, 32, "#f8fafc", True)
            centered(draw, (box[0] + 8, box[1] + 100, box[2] - 8, box[3] - 20), line, 19, stroke)
            if index < len(cards) - 1:
                arrow(draw, (box[2] + 10, 375), (cards[index + 1][0][0] - 10, 375), stroke)
        draw.rounded_rectangle((85, 610, 1415, 755), radius=24, fill="#0f172a", outline="#334155", width=3)
        draw.text((125, 646), "IMPORTANT BOUNDARY", font=pil_font(27, True), fill="#fbbf24")
        draw.text((125, 697), "No new GitHub, shell, credential, merge, deploy, or usage quota permission.", font=pil_font(24), fill="#e2e8f0")

    elif stem == "02-install-flow":
        steps = [
            ("1", "Unzip"), ("2", "Preview"), ("3", "Apply"), ("4", "Restart"), ("5", "Install plugin")
        ]
        colors_by_step = ["#60a5fa", "#facc15", "#2dd4bf", "#fb923c", "#c084fc"]
        for i, ((number, label), color) in enumerate(zip(steps, colors_by_step)):
            x = 90 + i * 285
            draw.ellipse((x, 260, x + 190, 450), fill="#111827", outline=color, width=5)
            centered(draw, (x, 275, x + 190, 365), number, 54, color, True)
            centered(draw, (x + 5, 350, x + 185, 425), label, 24, "#f8fafc", True)
            if i < 4:
                arrow(draw, (x + 200, 355), (x + 275, 355), "#64748b")
        draw.rounded_rectangle((105, 575, 1395, 730), radius=24, fill="#0f172a", outline="#334155", width=3)
        draw.text((140, 610), "Preview: powershell -ExecutionPolicy Bypass -File .\\Install-AEGISWebContinuation.ps1", font=pil_font(21), fill="#f8fafc")
        draw.text((140, 666), "Apply:   powershell -ExecutionPolicy Bypass -File .\\Install-AEGISWebContinuation.ps1 -Apply", font=pil_font(21), fill="#5eead4")

    elif stem == "03-mobile-handoff":
        cards = [
            ((80, 235, 420, 610), "Local PC", ["Review git status", "Stage exact files", "Commit checkpoint", "Push exact branch"], "#60a5fa"),
            ((580, 235, 920, 610), "GitHub", ["Repository identity", "Branch + commit SHA", "Issue / PR context", "Test results"], "#cbd5e1"),
            ((1080, 235, 1420, 610), "Phone / Web", ["Invoke @AEGIS", "Validate identity", "Load evidence", "Continue or block"], "#2dd4bf"),
        ]
        for i, (box, head, lines, color) in enumerate(cards):
            draw.rounded_rectangle(box, radius=28, fill="#111827", outline=color, width=4)
            draw.text((box[0] + 35, box[1] + 35), head, font=pil_font(34, True), fill=color)
            for line_index, line in enumerate(lines, 1):
                draw.text((box[0] + 35, box[1] + 105 + line_index * 48), f"{line_index}. {line}", font=pil_font(23), fill="#e2e8f0")
            if i < 2:
                arrow(draw, (box[2] + 15, 420), (cards[i + 1][0][0] - 15, 420), color)
        draw.rounded_rectangle((85, 690, 1415, 770), radius=20, fill="#3b1d0b", outline="#fb923c", width=3)
        centered(draw, (100, 700, 1400, 760), "Uncommitted local files are not visible while the PC is offline.", 25, "#ffedd5")

    else:
        centered(draw, (500, 190, 1000, 285), "CLI unavailable", 34, "#ffedd5", True)
        draw.rounded_rectangle((500, 190, 1000, 285), radius=24, outline="#fb923c", width=4)
        draw.line((750, 285, 750, 345), fill="#94a3b8", width=6)
        draw.rounded_rectangle((460, 345, 1040, 445), radius=24, fill="#172554", outline="#60a5fa", width=4)
        centered(draw, (460, 345, 1040, 445), "Latest checkpoint on GitHub?", 30, "#dbeafe", True)
        draw.line((460, 395, 265, 395, 265, 525), fill="#ef4444", width=6)
        draw.line((1040, 395, 1235, 395, 1235, 525), fill="#2dd4bf", width=6)
        draw.text((335, 350), "NO", font=pil_font(24, True), fill="#fca5a5")
        draw.text((1120, 350), "YES", font=pil_font(24, True), fill="#99f6e4")
        draw.rounded_rectangle((70, 525, 610, 675), radius=24, fill="#450a0a", outline="#ef4444", width=4)
        centered(draw, (70, 535, 610, 605), "BLOCKED_STALE_STATE", 29, "#fee2e2", True)
        centered(draw, (70, 600, 610, 660), "PC must publish a checkpoint", 22, "#fecaca")
        draw.rounded_rectangle((890, 525, 1430, 675), radius=24, fill="#052e2b", outline="#2dd4bf", width=4)
        centered(draw, (890, 535, 1430, 600), "Validate Web capability", 29, "#ccfbf1", True)
        centered(draw, (890, 595, 1430, 660), "Executor: continue | Read-only: handoff", 21, "#99f6e4")
        centered(draw, (400, 730, 1100, 795), "Never claim execution without diff and test evidence.", 24, "#f8fafc", True)

    image.save(output, "PNG", optimize=True)


def render_svg(svg: Path) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    png = TMP_DIR / f"{svg.stem}.png"
    diagram_png(svg.stem, png)
    return png


def add_page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("NotoSans", 8)
    canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"AEGIS Web Continuation | {doc.page}")
    canvas.restoreState()


def command_box(text: str, width: float) -> Table:
    table = Table([[Paragraph(text, STYLES["CodeBox"])]], colWidths=[width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#334155")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


BASE = getSampleStyleSheet()
STYLES = {
    "Title": ParagraphStyle(
        "Title",
        parent=BASE["Title"],
        fontName="NotoSans-Bold",
        fontSize=27,
        leading=32,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_CENTER,
        spaceAfter=12,
    ),
    "Subtitle": ParagraphStyle(
        "Subtitle",
        parent=BASE["Normal"],
        fontName="NotoSans",
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER,
        spaceAfter=12,
    ),
    "H1": ParagraphStyle(
        "H1",
        parent=BASE["Heading1"],
        fontName="NotoSans-Bold",
        fontSize=20,
        leading=25,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10,
    ),
    "Body": ParagraphStyle(
        "Body",
        parent=BASE["BodyText"],
        fontName="NotoSans",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=7,
    ),
    "Bullet": ParagraphStyle(
        "Bullet",
        parent=BASE["BodyText"],
        fontName="NotoSans",
        fontSize=10.5,
        leading=15,
        leftIndent=14,
        firstLineIndent=-8,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5,
    ),
    "CodeBox": ParagraphStyle(
        "CodeBox",
        parent=BASE["Code"],
        fontName="DejaVuSansMono",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#e2e8f0"),
        alignment=TA_LEFT,
    ),
    "Note": ParagraphStyle(
        "Note",
        parent=BASE["BodyText"],
        fontName="NotoSans-Bold",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#9a3412"),
        borderColor=colors.HexColor("#fdba74"),
        borderWidth=0.8,
        borderPadding=9,
        backColor=colors.HexColor("#fff7ed"),
        spaceBefore=8,
        spaceAfter=8,
    ),
}


def build() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    diagrams = [render_svg(IMAGE_DIR / name) for name in (
        "01-system-overview.svg",
        "02-install-flow.svg",
        "03-mobile-handoff.svg",
        "04-cli-fallback.svg",
    )]

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="AEGIS Web Continuation Visual Guide",
        author="AEGIS Workflow",
        subject="Visual setup and mobile continuation guide",
    )
    usable_width = A4[0] - 32 * mm
    story = [
        Spacer(1, 14 * mm),
        Paragraph("AEGIS Web Continuation", STYLES["Title"]),
        Paragraph("Visual setup and mobile continuation guide", STYLES["Subtitle"]),
        Spacer(1, 7 * mm),
        Image(str(diagrams[0]), width=usable_width, height=usable_width * 675 / 1200),
        Spacer(1, 7 * mm),
        Paragraph(
            "This visual companion uses English labels for maximum PDF compatibility. "
            "The complete Thai instructions are in docs/USER_GUIDE_TH.md inside the same package.",
            STYLES["Note"],
        ),
        PageBreak(),
        Paragraph("1. Install on Windows", STYLES["H1"]),
        Image(str(diagrams[1]), width=usable_width, height=usable_width * 675 / 1200),
        Spacer(1, 6 * mm),
        Paragraph("Run the preview first and confirm PREVIEW_ONLY before applying changes.", STYLES["Body"]),
        command_box("powershell -ExecutionPolicy Bypass -File .\\Install-AEGISWebContinuation.ps1", usable_width),
        Spacer(1, 3 * mm),
        command_box("powershell -ExecutionPolicy Bypass -File .\\Install-AEGISWebContinuation.ps1 -Apply", usable_width),
        Paragraph(
            "Restart ChatGPT desktop, open Plugins, choose Personal, install AEGIS Web Continuation, and start a new chat.",
            STYLES["Body"],
        ),
        PageBreak(),
        Paragraph("2. Connect repository execution", STYLES["H1"]),
        Paragraph("1. Open Codex cloud and sign in with the intended ChatGPT account.", STYLES["Bullet"]),
        Paragraph("2. Connect GitHub and select only the repository you authorize.", STYLES["Bullet"]),
        Paragraph("3. Create an environment for that repository.", STYLES["Bullet"]),
        Paragraph("4. Configure only real dependencies, variables, and secrets required by the project.", STYLES["Bullet"]),
        Paragraph("5. Start with a read-only identity check for repository, branch, and HEAD commit.", STYLES["Bullet"]),
        Spacer(1, 4 * mm),
        command_box(
            "Inspect repository, branch, and HEAD commit only.<br/>"
            "Do not edit, create files, push, or open a PR.<br/>"
            "Report the repository capabilities available in this session.",
            usable_width,
        ),
        Paragraph(
            "The Skill is workflow guidance. Codex cloud supplies repository tools only after the repository and environment are authorized.",
            STYLES["Note"],
        ),
        PageBreak(),
        Paragraph("3. Hand off work before leaving the PC", STYLES["H1"]),
        Image(str(diagrams[2]), width=usable_width, height=usable_width * 675 / 1200),
        Spacer(1, 5 * mm),
        command_box("git status --short<br/>git branch --show-current<br/>git rev-parse HEAD", usable_width),
        Paragraph(
            "Commit and push only reviewed files to the exact branch. Uncommitted local files are not visible from the phone while the PC is offline.",
            STYLES["Note"],
        ),
        PageBreak(),
        Paragraph("4. Continue from phone or web", STYLES["H1"]),
        command_box(
            "@AEGIS Web Continuation<br/>"
            "Continue repository &lt;owner/repo&gt; on branch &lt;exact-branch&gt;.<br/>"
            "Use commit &lt;exact-sha&gt; and Issue/PR &lt;URL-or-number&gt;.<br/>"
            "Validate repository identity and checkpoint before mutation.<br/>"
            "Propose a Mutation Plan, run targeted checks, and return diff plus verification.<br/>"
            "Do not merge, push, deploy, or access credentials without explicit approval.",
            usable_width,
        ),
        Spacer(1, 7 * mm),
        Paragraph("Expected statuses", STYLES["H1"]),
        Table(
            [
                ["Status", "Meaning"],
                ["READY_TO_CONTINUE", "Identity, scope, and evidence are sufficient."],
                ["BLOCKED_REPO_ACCESS", "The current session cannot access the repository."],
                ["BLOCKED_STALE_STATE", "Commit, evidence, or checkpoint is out of date."],
                ["BLOCKED_SECURITY_CONFLICT", "The requested task conflicts with a security rule."],
                ["NEEDS_APPROVAL", "A protected operation requires explicit user approval."],
                ["READY_REVIEW", "Diff and verification evidence are ready for review."],
            ],
            colWidths=[58 * mm, usable_width - 58 * mm],
            repeatRows=1,
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "NotoSans-Bold"),
                    ("FONTNAME", (0, 1), (0, -1), "DejaVuSansMono-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        ),
        PageBreak(),
        Paragraph("5. CLI usage-limit fallback", STYLES["H1"]),
        Image(str(diagrams[3]), width=usable_width, height=usable_width * 675 / 1200),
        Spacer(1, 5 * mm),
        Paragraph("If the latest checkpoint is on GitHub and Codex cloud tools are available, validate identity and continue.", STYLES["Bullet"]),
        Paragraph("If the latest work exists only on an offline PC, stop with BLOCKED_STALE_STATE.", STYLES["Bullet"]),
        Paragraph("If the web session is read-only, produce analysis or a handoff; do not claim repository mutation.", STYLES["Bullet"]),
        Paragraph("The Skill cannot bypass or replenish ChatGPT/Codex usage limits.", STYLES["Note"]),
        PageBreak(),
        Paragraph("6. Go-live checklist", STYLES["H1"]),
    ]
    checklist = [
        "Installer preview shows no conflict.",
        "Plugin appears in the desktop Plugins Directory.",
        "A new chat can invoke the Skill with @.",
        "The target web/mobile account can see the Skill.",
        "GitHub is connected only to the intended repository.",
        "Codex cloud environment opens the correct repository.",
        "Read-only identity test reports the correct branch and commit.",
        "A small executor-mode task produces a reviewable diff and test evidence.",
        "Merge, push, deploy, credentials, and network remain approval-gated.",
    ]
    story.extend(Paragraph(f"[ ] {item}", STYLES["Bullet"]) for item in checklist)
    story.extend(
        [
            Spacer(1, 6 * mm),
            Paragraph("Official documentation", STYLES["H1"]),
            Paragraph("https://learn.chatgpt.com/docs/build-skills", STYLES["Body"]),
            Paragraph("https://learn.chatgpt.com/docs/plugins", STYLES["Body"]),
            Paragraph("https://learn.chatgpt.com/docs/cloud", STYLES["Body"]),
            Paragraph("https://developers.openai.com/plugins/build/plugins", STYLES["Body"]),
        ]
    )
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(OUTPUT)


if __name__ == "__main__":
    build()
