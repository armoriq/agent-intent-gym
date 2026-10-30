from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase.pdfmetrics import stringWidth


OUTPUT = "/Users/psudokit/benchmark/output/pdf/LLM_Token_Benchmarking_Minor_Project_Synopsis.pdf"
LOGO = "/Users/psudokit/benchmark/tmp/pdfs/assets/vips-000.jpg"


class SynopsisDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=0.65 * inch,
            rightMargin=0.65 * inch,
            topMargin=0.52 * inch,
            bottomMargin=0.52 * inch,
            title="A User-Centric Framework for Benchmarking Token Efficiency, Guardrails and Policy Compliance in Large Language Models",
            author="Pulkit Saraf, Bans Nagpal and Manasvi",
            subject="Minor Project Synopsis, School of Engineering & Technology, VIPS-TC",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="main",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates([PageTemplate(id="synopsis", frames=[frame], onPage=self.footer)])

    def footer(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        y = 0.25 * inch
        canvas.setStrokeColor(colors.HexColor("#A8A8A8"))
        canvas.setLineWidth(0.4)
        canvas.line(self.leftMargin, y + 8, letter[0] - self.rightMargin, y + 8)
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(self.leftMargin, y, "Minor Project Synopsis")
        footer_text = f"Page {doc.page} of 6"
        canvas.drawRightString(letter[0] - self.rightMargin, y, footer_text)
        canvas.restoreState()


styles = getSampleStyleSheet()
body = ParagraphStyle(
    "Body",
    fontName="Times-Roman",
    fontSize=12,
    leading=18,
    alignment=TA_JUSTIFY,
    spaceAfter=5,
    textColor=colors.black,
)
body_compact = ParagraphStyle(
    "BodyCompact",
    parent=body,
    leading=17,
    spaceAfter=5,
)
chapter = ParagraphStyle(
    "Chapter",
    fontName="Times-Bold",
    fontSize=16,
    leading=20,
    alignment=TA_CENTER,
    spaceAfter=10,
)
heading = ParagraphStyle(
    "Heading",
    fontName="Times-Bold",
    fontSize=14,
    leading=17,
    alignment=TA_LEFT,
    spaceBefore=5,
    spaceAfter=4,
)
subheading = ParagraphStyle(
    "Subheading",
    fontName="Times-Bold",
    fontSize=12,
    leading=16,
    alignment=TA_LEFT,
    spaceBefore=4,
    spaceAfter=2,
)
bullet = ParagraphStyle(
    "Bullet",
    parent=body_compact,
    leftIndent=16,
    firstLineIndent=-10,
    bulletIndent=5,
    spaceAfter=2,
)
small = ParagraphStyle(
    "Small",
    fontName="Times-Roman",
    fontSize=10.5,
    leading=14,
    alignment=TA_LEFT,
    spaceAfter=4,
)
reference = ParagraphStyle(
    "Reference",
    fontName="Times-Roman",
    fontSize=10.5,
    leading=14,
    alignment=TA_JUSTIFY,
    leftIndent=18,
    firstLineIndent=-18,
    spaceAfter=6,
)


def P(text, style=body):
    return Paragraph(text, style)


def B(text):
    return Paragraph(text, bullet, bulletText="-")


def section(title, content):
    return KeepTogether([P(title, heading)] + content)


story = []

# Cover page
story += [
    Spacer(1, 0.36 * inch),
    P(
        "A User-Centric Framework for Benchmarking<br/>"
        "Token Efficiency, Guardrails and Policy Compliance<br/>"
        "in Large Language Models",
        ParagraphStyle(
            "CoverTitle",
            fontName="Times-Bold",
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            spaceAfter=23,
        ),
    ),
    Image(LOGO, width=1.2 * inch, height=0.79 * inch),
    Spacer(1, 0.14 * inch),
    P(
        '<font color="#E32020"><b>VIVEKANANDA INSTITUTE OF PROFESSIONAL STUDIES - TECHNICAL CAMPUS</b></font><br/>'
        '<font size="10"><b>Grade A++ Accredited Institution by NAAC</b><br/>'
        'NBA Accredited for MCA Programme; Recognized under Section 2(f) by UGC;<br/>'
        'Affiliated to GGSIP University, Delhi; Recognized by Bar Council of India and AICTE<br/>'
        'An ISO 9001:2015 Certified Institution</font><br/>'
        '<font color="#009FE3"><b>SCHOOL OF ENGINEERING &amp; TECHNOLOGY</b></font>',
        ParagraphStyle("Institute", parent=small, alignment=TA_CENTER, leading=12, spaceAfter=0),
    ),
    Spacer(1, 0.40 * inch),
    P("Under the supervision of", ParagraphStyle("CoverLabel", parent=body, alignment=TA_CENTER, fontSize=15, spaceAfter=9)),
    P("Himika", ParagraphStyle("CoverValue", parent=body, fontName="Times-Bold", alignment=TA_CENTER, fontSize=15)),
    Spacer(1, 0.22 * inch),
    P("by", ParagraphStyle("CoverBy", parent=body, alignment=TA_CENTER, fontSize=14)),
    P(
        "Pulkit Saraf, 10617702723<br/>"
        "Bans Nagpal, 20117702723<br/>"
        "Manasvi, 35417702723",
        ParagraphStyle("CoverStudent", parent=body, fontName="Times-Bold", alignment=TA_CENTER, fontSize=14, leading=20),
    ),
    Spacer(1, 0.62 * inch),
    P(
        "School of Engineering &amp; Technology<br/>"
        "Vivekananda Institute of Professional Studies - Technical Campus<br/>"
        "Pitampura, Delhi - 110034<br/><b>Academic Session 2026-27</b>",
        ParagraphStyle("CoverFooter", parent=body, alignment=TA_CENTER, fontSize=13, leading=17),
    ),
    PageBreak(),
]

# Page 2: contents + introduction
story += [
    P("TABLE OF CONTENTS", chapter),
]
toc_data = [
    [P("Section", subheading), P("Page", subheading), P("Justification", subheading)],
    [P("1. Introduction and Literature Review", small), P("3", small), P("Defines tokens, evaluation dimensions and the research gap.", small)],
    [P("2. Problem Statement and Feasibility Study", small), P("4", small), P("States the research questions and a reproducible evaluation design.", small)],
    [P("3. Hardware and Software Requirements", small), P("5", small), P("Specifies the resources, deliverables, limitations and schedule.", small)],
    [P("4. References", small), P("6", small), P("Provides the scholarly and standards basis in IEEE format.", small)],
]
toc = Table(toc_data, colWidths=[2.15 * inch, 0.55 * inch, 3.55 * inch], repeatRows=1, hAlign="CENTER")
toc.setStyle(
    TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
)
story += [toc, PageBreak(), P("1. INTRODUCTION AND LITERATURE REVIEW", chapter)]
story += [
    P(
        "Large language models (LLMs) transform text into tokens - subword units produced by a tokenizer - and predict a sequence of output tokens using transformer-based attention [1], [2]. Tokens are therefore both computational units and billing units. Two systems may answer the same request with different token counts because of tokenizer design, hidden reasoning, prompt construction, context handling and response length. A useful comparison must consequently measure task success together with input tokens, output tokens, latency, cost and safety behavior rather than reporting accuracy alone."
    ),
    P(
        "Existing work provides strong foundations but leaves a practical gap. HELM advocates scenario coverage and multiple metrics [3]. MT-Bench and Chatbot Arena use preference evaluation while documenting position, verbosity and self-enhancement biases in LLM judges [4]. LiveBench addresses contamination with refreshed, objectively scored questions [5]. Yet public leaderboards may remain unlike everyday work, and one aggregate rank can hide task-specific trade-offs."
    ),
    P("Research Aim", heading),
    P(
        "The project will design and pilot a transparent benchmark for accessible LLMs and AI products on realistic tasks, token efficiency, prompt optimization, guardrails and policy compliance. It will publish prompts, rubrics, settings, outputs and uncertainty so results are reproducible rather than a universal rank.",
        body_compact,
    ),
    P("Objectives", heading),
    B("Create a balanced suite covering knowledge work, coding, reasoning, multilingual use, long context and safety-sensitive requests."),
    B("Measure quality, factuality, adherence, robustness, latency, tokens, cost, safe refusal and over-refusal."),
    B("Compare baseline prompts with structured prompts and context reduction."),
    B("Separate base-model effects from product, agent, tool and guardrail effects."),
    PageBreak(),
]

# Page 3: problem and methodology
story += [P("2. PROBLEM STATEMENT AND FEASIBILITY STUDY", chapter)]
story += [
    P("Problem Statement", heading),
    P(
        "Providers and benchmark platforms use different prompts, judges, sampling settings and reporting rules. Static tasks may be contaminated; subjective judges may favor verbosity or their own model family; and products may add hidden prompts, retrieval, tools or safety filters. Thus, a leaderboard may not predict the most effective, economical and safe system for a real task. The problem is to expose these confounders and report task-level trade-offs."
    ),
    P("Research Questions", heading),
    B("RQ1: How do quality, latency, token consumption and cost vary for the same real-life task?"),
    B("RQ2: Do rankings change by task, language, context length and native product versus controlled API?"),
    B("RQ3: Which prompt/context optimizations reduce tokens without materially reducing task success?"),
    B("RQ4: How do guardrails affect unsafe compliance, appropriate refusal, over-refusal and stability under prompt variations?"),
    P("Proposed Model and Product Scope", heading),
    P(
        "The pilot will use exact, dated identifiers and lawful access. Candidates are Anthropic Claude (Opus, Fable and Sonnet), OpenAI ChatGPT/API or Codex-served variants (including accessible Luna and Terra tiers), Cursor Composer workflows, Zhipu GLM and Moonshot Kimi. Any '0xAlpha' entry requires verified identity. Composer and Composio-integrated workflows will be product/orchestration conditions, not base models.",
        body_compact,
    ),
    P("Experimental Design", heading),
    B("Two tracks: (A) controlled API tests with the same user prompt and matched settings where supported; (B) native-product tests with default user-visible behavior."),
    B("24 tasks in six categories, three runs per task and prompt variants; eight systems yield 576 core observations."),
    B("Automatic checks for code, exact answers and format; blind human rubrics for open work; LLM judging only as secondary evidence."),
    B("Random order, anonymous labels, no self-judging, fixed rubrics, version/date logs and bootstrap confidence intervals."),
    B("Primary result: cost and tokens per successful task. Secondary: quality, pass rate, factual errors, p50/p95 latency, robustness, refusal precision and over-refusal."),
    P("Hypotheses", heading),
    P(
        "H1: more tokens will not always yield proportionally better outcomes. H2: no model will dominate every task. H3: stronger guardrails will reduce unsafe compliance but may increase over-refusal.",
        body_compact,
    ),
    PageBreak(),
]

# Page 4: feasibility, requirements, outcomes
story += [P("3. HARDWARE AND SOFTWARE REQUIREMENTS", chapter)]
story += [
    P("Feasibility Study", heading),
    P(
        "Most candidates are cloud-hosted and accessible by official APIs or interfaces. A standard laptop can run the benchmark, logs and scoring. A small pilot, output limits, permitted caching and a pre-declared cap support financial feasibility. Automation plus a limited blind review supports operational feasibility. No model training or high-end GPU is required.",
        body_compact,
    ),
    P("Hardware Requirements", heading),
]
hardware = Table(
    [
        [P("Component", subheading), P("Minimum / Recommended", subheading)],
        [P("Computer", small), P("64-bit, 4-core laptop; 8 GB RAM minimum, 16 GB recommended", small)],
        [P("Storage / Network", small), P("10 GB free storage and stable broadband", small)],
        [P("Optional", small), P("GPU only if an open-weight local baseline is added", small)],
    ],
    colWidths=[1.45 * inch, 4.65 * inch],
    hAlign="CENTER",
)
hardware.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#888888")),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story += [hardware, P("Software Requirements", heading)]
software = Table(
    [
        [P("Category", subheading), P("Proposed Tools", subheading)],
        [P("Runtime", small), P("Python 3.11+; official vendor SDKs or HTTPS clients", small)],
        [P("Data / analysis", small), P("JSONL/CSV, pandas, NumPy, SciPy and Jupyter", small)],
        [P("Usage logging", small), P("Provider metadata, available tokenizers and a dated price table", small)],
        [P("Evaluation", small), P("pytest/validators, rubric forms and optional secondary judge", small)],
        [P("Reproducibility", small), P("Git, lock file, run manifest and model/version timestamps", small)],
        [P("Reporting", small), P("Matplotlib/Seaborn and PDF tools", small)],
    ],
    colWidths=[1.45 * inch, 4.65 * inch],
    hAlign="CENTER",
)
software.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#888888")),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story += [software]
story += [
    P("Expected Outcomes", heading),
    B("An open specification, reusable tasks, scoring rubric and experiment manifest."),
    B("Task/category results with confidence intervals, plus a token-quality-cost frontier."),
    B("Practical guidance for model selection, prompt optimization and guardrail calibration."),
    P("Limitations and Ethics", heading),
    P(
        "Results will be time-bound; interfaces may not be equivalent; hidden prompts/tokenizers may be inaccessible; and human scoring remains subjective. The study will avoid personal data, respect provider terms, use synthetic safety prompts, disclose constraints and withhold harmful operational detail. Safety evaluation follows NIST risk-based guidance [7].",
        body_compact,
    ),
    P("Indicative Work Plan", heading),
    P(
        "Weeks 1-2: review/protocol; 3-4: tasks/rubrics; 5-6: runner/pilot; 7-8: data collection; 9-10: analysis; 11-12: paper, repository and presentation.",
        body_compact,
    ),
    PageBreak(),
]

# Page 5: references
story += [P("4. REFERENCES", chapter)]
refs = [
    "[1] A. Vaswani <i>et al.</i>, \"Attention Is All You Need,\" in <i>Advances in Neural Information Processing Systems</i>, vol. 30, 2017, pp. 5998-6008.",
    "[2] T. Kudo and J. Richardson, \"SentencePiece: A simple and language independent subword tokenizer and detokenizer for Neural Text Processing,\" in <i>Proc. 2018 Conf. Empirical Methods in Natural Language Processing: System Demonstrations</i>, Brussels, Belgium, 2018, pp. 66-71, doi: 10.18653/v1/D18-2012.",
    "[3] P. Liang <i>et al.</i>, \"Holistic Evaluation of Language Models,\" <i>Transactions on Machine Learning Research</i>, 2023. [Online]. Available: https://arxiv.org/abs/2211.09110",
    "[4] L. Zheng <i>et al.</i>, \"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,\" in <i>Advances in Neural Information Processing Systems</i>, vol. 36, 2023, pp. 46595-46623.",
    "[5] C. White <i>et al.</i>, \"LiveBench: A Challenging, Contamination-Free LLM Benchmark,\" arXiv:2406.19314, 2024. [Online]. Available: https://arxiv.org/abs/2406.19314",
    "[6] Y. Bai <i>et al.</i>, \"Constitutional AI: Harmlessness from AI Feedback,\" arXiv:2212.08073, 2022. [Online]. Available: https://arxiv.org/abs/2212.08073",
    "[7] C. Autio <i>et al.</i>, <i>Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile</i>, NIST AI 600-1, National Institute of Standards and Technology, Gaithersburg, MD, USA, Jul. 2024, doi: 10.6028/NIST.AI.600-1.",
    "[8] W.-L. Chiang <i>et al.</i>, \"Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference,\" in <i>Proc. 41st Int. Conf. Machine Learning</i>, Vienna, Austria, 2024, pp. 8359-8388.",
]
for ref in refs:
    story.append(P(ref, reference))

story += [
    Spacer(1, 0.15 * inch),
    P("Proposed Keywords", heading),
    P(
        "Large language models; tokenization; benchmarking; token efficiency; prompt optimization; guardrails; policy compliance; human evaluation; reproducibility.",
        body,
    ),
    Spacer(1, 0.18 * inch),
    P(
        "Note: The exact model versions, access routes, prices and product settings will be frozen and recorded at the start of data collection. This prevents later model updates from being mixed into the same experimental condition.",
        ParagraphStyle("Note", parent=small, fontName="Times-Italic", leading=15, alignment=TA_JUSTIFY),
    ),
]


doc = SynopsisDoc(OUTPUT)
doc.build(story)
print(OUTPUT)
