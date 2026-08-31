from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# =========================================================
# CORES
# =========================================================

NAVY = colors.HexColor("#111827")
BLUE = colors.HexColor("#304B85")
ACCENT = colors.HexColor("#4F6FFF")
TEXT = colors.HexColor("#344054")
MUTED = colors.HexColor("#667085")
LIGHT = colors.HexColor("#F7F9FC")
BORDER = colors.HexColor("#E3E8F0")
GREEN_BG = colors.HexColor("#E8FFF2")
GREEN = colors.HexColor("#087443")
AMBER_BG = colors.HexColor("#FFF7E6")
AMBER = colors.HexColor("#9A6700")


# =========================================================
# HELPERS
# =========================================================

def _safe(value: Any, default: str = "Não identificado") -> str:
    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def _items(values: Any) -> list[str]:
    if not values:
        return []

    return [
        str(item).strip()
        for item in values
        if str(item).strip()
    ]


def _bullet_text(values: Any) -> str:
    items = _items(values)

    if not items:
        return "Não identificado."

    return "<br/>".join(
        f"• {item}"
        for item in items
    )


# =========================================================
# ESTILOS
# =========================================================

def _build_styles():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "CC_Title",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=colors.white,
            spaceAfter=6,
        ),

        "subtitle": ParagraphStyle(
            "CC_Subtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=14,
            textColor=colors.HexColor("#D9E0EF"),
        ),

        "eyebrow": ParagraphStyle(
            "CC_Eyebrow",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=10,
            textColor=colors.HexColor("#A9BBFF"),
            spaceAfter=8,
        ),

        "section": ParagraphStyle(
            "CC_Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=8,
        ),

        "subsection": ParagraphStyle(
            "CC_Subsection",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=NAVY,
            spaceAfter=5,
        ),

        "body": ParagraphStyle(
            "CC_Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=13,
            textColor=TEXT,
        ),

        "small": ParagraphStyle(
            "CC_Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=11,
            textColor=MUTED,
        ),

        "metric_label": ParagraphStyle(
            "CC_Metric_Label",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=MUTED,
        ),

        "metric_value": ParagraphStyle(
            "CC_Metric_Value",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=NAVY,
        ),

        "center_small": ParagraphStyle(
            "CC_Center",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontName="Helvetica",
            fontSize=7,
            leading=10,
            textColor=MUTED,
        ),
    }


# =========================================================
# HEADER / FOOTER
# =========================================================

def _draw_page(canvas, doc):
    canvas.saveState()

    width, height = A4

    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)

    canvas.line(
        18 * mm,
        14 * mm,
        width - 18 * mm,
        14 * mm,
    )

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)

    canvas.drawString(
        18 * mm,
        9 * mm,
        "CareerCompass AI · Career Intelligence Platform",
    )

    canvas.drawRightString(
        width - 18 * mm,
        9 * mm,
        f"Página {doc.page}",
    )

    canvas.restoreState()


# =========================================================
# COMPONENTES
# =========================================================

def _section_title(text: str, styles):
    return [
        Spacer(1, 4 * mm),
        Paragraph(text, styles["section"]),
        HRFlowable(
            width="100%",
            thickness=0.6,
            color=BORDER,
            spaceAfter=4 * mm,
        ),
    ]


def _metric_card(label: str, value: str, styles):
    content = [
        Paragraph(label, styles["metric_label"]),
        Spacer(1, 1.5 * mm),
        Paragraph(value, styles["metric_value"]),
    ]

    table = Table(
        [[content]],
        colWidths=[52 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )

    return table


def _info_box(title: str, content: str, styles):
    body = [
        Paragraph(title, styles["subsection"]),
        Paragraph(content, styles["body"]),
    ]

    table = Table(
        [[body]],
        colWidths=[170 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )

    return table


def _diagnostic_box(
    title: str,
    items: Any,
    styles,
    positive: bool = True,
):
    background = GREEN_BG if positive else AMBER_BG
    foreground = GREEN if positive else AMBER

    body = [
        Paragraph(
            f"<font color='{foreground.hexval()}'><b>{title}</b></font>",
            styles["subsection"],
        ),
        Spacer(1, 1 * mm),
        Paragraph(
            _bullet_text(items),
            styles["body"],
        ),
    ]

    table = Table(
        [[body]],
        colWidths=[82 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.5, foreground),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )

    return table


# =========================================================
# PDF
# =========================================================

def build_career_report_pdf(report) -> bytes:
    """
    Gera o Career Assessment Report em PDF e retorna os bytes.
    """

    buffer = BytesIO()
    styles = _build_styles()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title="CareerCompass AI - Career Assessment Report",
        author="CareerCompass AI",
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )

    template = PageTemplate(
        id="careercompass",
        frames=[frame],
        onPage=_draw_page,
    )

    doc.addPageTemplates([template])

    story = []

    # =====================================================
    # HERO
    # =====================================================

    hero_content = [
        Paragraph(
            "CAREER INTELLIGENCE PLATFORM",
            styles["eyebrow"],
        ),
        Paragraph(
            "Career Assessment Report",
            styles["title"],
        ),
        Paragraph(
            "Diagnóstico profissional estruturado a partir das "
            "informações analisadas pelo CareerCompass AI.",
            styles["subtitle"],
        ),
    ]

    hero = Table(
        [[hero_content]],
        colWidths=[170 * mm],
    )

    hero.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 8 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8 * mm),
            ]
        )
    )

    story.append(hero)
    story.append(Spacer(1, 7 * mm))

    # =====================================================
    # IDENTIFICAÇÃO
    # =====================================================

    story.extend(
        _section_title(
            "1. Identificação do Assessment",
            styles,
        )
    )

    identification = (
        f"<b>Candidato:</b> {_safe(report.candidate_name)}<br/>"
        f"<b>Fonte analisada:</b> {_safe(report.source_name)}<br/>"
        f"<b>Data da análise:</b> {_safe(report.generated_at)}"
    )

    story.append(
        _info_box(
            "Informações da análise",
            identification,
            styles,
        )
    )

    story.append(Spacer(1, 6 * mm))

    # =====================================================
    # MÉTRICAS
    # =====================================================

    metrics = Table(
        [
            [
                _metric_card(
                    "Senioridade",
                    _safe(report.seniority),
                    styles,
                ),
                _metric_card(
                    "Áreas identificadas",
                    str(len(_items(report.areas))),
                    styles,
                ),
                _metric_card(
                    "Caminhos sugeridos",
                    str(len(report.recommended_roles or [])),
                    styles,
                ),
            ]
        ],
        colWidths=[
            56 * mm,
            56 * mm,
            56 * mm,
        ],
    )

    metrics.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
            ]
        )
    )

    story.append(metrics)

    # =====================================================
    # PERFIL
    # =====================================================

    story.extend(
        _section_title(
            "2. Perfil Profissional Identificado",
            styles,
        )
    )

    story.append(
        _info_box(
            "Áreas de atuação",
            _bullet_text(report.areas),
            styles,
        )
    )

    story.append(Spacer(1, 3 * mm))

    story.append(
        _info_box(
            "Hard Skills",
            _bullet_text(report.hard_skills),
            styles,
        )
    )

    story.append(Spacer(1, 3 * mm))

    story.append(
        _info_box(
            "Ferramentas e tecnologias",
            _bullet_text(report.tools),
            styles,
        )
    )

    # =====================================================
    # GESTÃO
    # =====================================================

    story.extend(
        _section_title(
            "3. Gestão e Competências Complementares",
            styles,
        )
    )

    story.append(
        _info_box(
            "Gestão e liderança",
            _bullet_text(report.management_skills),
            styles,
        )
    )

    story.append(Spacer(1, 3 * mm))

    story.append(
        _info_box(
            "Metodologias",
            _bullet_text(report.methodologies),
            styles,
        )
    )

    story.append(Spacer(1, 3 * mm))

    story.append(
        _info_box(
            "Idiomas",
            _bullet_text(report.languages),
            styles,
        )
    )

    # =====================================================
    # EVIDÊNCIAS
    # =====================================================

    story.extend(
        _section_title(
            "4. Evidências Profissionais",
            styles,
        )
    )

    story.append(
        _info_box(
            "Evidências identificadas no perfil",
            _bullet_text(report.evidence_terms),
            styles,
        )
    )

    # =====================================================
    # DIAGNÓSTICO
    # =====================================================

    story.extend(
        _section_title(
            "5. Diagnóstico Profissional",
            styles,
        )
    )

    diagnostic = Table(
        [
            [
                _diagnostic_box(
                    "Principais forças",
                    report.strengths,
                    styles,
                    positive=True,
                ),
                _diagnostic_box(
                    "Pontos de atenção",
                    report.attention_points,
                    styles,
                    positive=False,
                ),
            ]
        ],
        colWidths=[85 * mm, 85 * mm],
    )

    diagnostic.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )

    story.append(diagnostic)

    # =====================================================
    # CAMINHOS
    # =====================================================

    story.extend(
        _section_title(
            "6. Caminhos Profissionais",
            styles,
        )
    )

    roles = report.recommended_roles or []

    if roles:

        for position, role in enumerate(
            roles,
            start=1,
        ):
            title = _safe(
                role.get("title")
                if isinstance(role, dict)
                else getattr(role, "title", None)
            )

            score = (
                role.get("score")
                if isinstance(role, dict)
                else getattr(role, "score", None)
            )

            level = _safe(
                role.get("level")
                if isinstance(role, dict)
                else getattr(role, "level", None)
            )

            reason = _safe(
                role.get("reason")
                if isinstance(role, dict)
                else getattr(role, "reason", None),
                default="",
            )

            score_text = (
                f"{score}%"
                if score is not None
                else "—"
            )

            role_content = [
                Paragraph(
                    f"{position}. {title}",
                    styles["subsection"],
                ),
                Paragraph(
                    f"<b>Aderência:</b> {score_text} &nbsp;&nbsp; "
                    f"<b>Classificação:</b> {level}",
                    styles["body"],
                ),
            ]

            if reason:
                role_content.append(
                    Spacer(1, 1.5 * mm)
                )

                role_content.append(
                    Paragraph(
                        reason,
                        styles["small"],
                    )
                )

            role_table = Table(
                [[role_content]],
                colWidths=[170 * mm],
            )

            role_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                        ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                    ]
                )
            )

            story.append(
                KeepTogether(role_table)
            )

            story.append(
                Spacer(1, 2.5 * mm)
            )

    else:

        story.append(
            _info_box(
                "Radar de Oportunidades",
                "Execute o Radar de Oportunidades para incluir "
                "recomendações de caminhos profissionais neste relatório.",
                styles,
            )
        )

    # =====================================================
    # RECOMENDAÇÕES
    # =====================================================

    story.extend(
        _section_title(
            "7. Recomendações",
            styles,
        )
    )

    story.append(
        _info_box(
            "Próximos passos sugeridos",
            _bullet_text(report.recommendations),
            styles,
        )
    )

    story.append(Spacer(1, 8 * mm))

    story.append(
        Paragraph(
            "Relatório gerado pelo CareerCompass AI. "
            "As informações apresentadas constituem apoio à análise "
            "profissional e não substituem avaliação humana especializada.",
            styles["center_small"],
        )
    )

    doc.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
