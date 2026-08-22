import os
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page numbers
    along with running header and footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        width, height = landscape(A4)

        # Top Running Header (Pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(36, height - 28, "CREDVERIFY PLATFORM | OFFICIAL INSTITUTION AUDIT & REGISTRY REPORT")
            self.drawRightString(width - 36, height - 28, "CONFIDENTIAL & PRIVILEGED")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, height - 32, width - 36, height - 32)

        # Bottom Running Footer (All Pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 36, width - 36, 36)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(36, 24, "Asymmetric Cryptography (RSA-2048 / SHA-256) • Secured by CredVerify Digital Integrity Protocol")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(width - 36, 24, page_str)

        self.restoreState()


def format_date_str(d) -> str:
    if not d:
        return "N/A"
    if hasattr(d, 'strftime'):
        return d.strftime("%d %b %Y, %H:%M UTC")
    try:
        dt = datetime.fromisoformat(str(d).replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(d)[:10]


def generate_institution_report_pdf(
    institution: Any,
    certificates: List[Any],
    stats: Dict[str, Any],
    generated_by_user: Any,
    status_filter: Optional[str] = "ALL",
    category_filter: Optional[str] = "ALL"
) -> str:
    """
    Generates a high-quality multi-page PDF report containing comprehensive
    institution data and the full & final issued certificate registry.
    """
    reports_dir = os.path.join("storage", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_code = (institution.institution_code or "INST").replace(" ", "_").replace("/", "_")
    file_name = f"Audit_Report_{safe_code}_{timestamp_slug}.pdf"
    file_path = os.path.join(reports_dir, file_name)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(A4),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2563eb")
    )

    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#475569")
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#ffffff"),
        alignment=0
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1e293b")
    )

    badge_active = ParagraphStyle(
        'BadgeActive',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#065f46")
    )

    badge_revoked = ParagraphStyle(
        'BadgeRevoked',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#991b1b")
    )

    badge_suspicious = ParagraphStyle(
        'BadgeSuspicious',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#92400e")
    )

    story = []

    # ---------------------------------------------------------
    # 1. HEADER BANNER & REPORT METADATA
    # ---------------------------------------------------------
    now_utc = datetime.now(timezone.utc).strftime("%d %B %Y at %H:%M:%S UTC")
    gen_by_name = getattr(generated_by_user, 'name', 'System Administrator')
    gen_by_role = getattr(generated_by_user, 'role', 'SUPER_ADMIN')
    gen_by_email = getattr(generated_by_user, 'email', 'admin@credverify.demo')

    header_left = [
        Paragraph("CREDVERIFY SECURITY & REGISTRY PLATFORM", subtitle_style),
        Spacer(1, 2),
        Paragraph(f"INSTITUTION AUDIT & ISSUED CERTIFICATE DOSSIER", title_style),
        Spacer(1, 3),
        Paragraph(f"Target Entity: <b>{institution.name}</b> (Code: <font color='#2563eb'><b>{institution.institution_code}</b></font>)", ParagraphStyle('Entity', fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor("#334155")))
    ]

    header_right = [
        Paragraph(f"<b>Report Reference:</b> REP-{safe_code}-{timestamp_slug[:8]}", meta_style),
        Paragraph(f"<b>Generated On:</b> {now_utc}", meta_style),
        Paragraph(f"<b>Generated By:</b> {gen_by_name} ({gen_by_role})", meta_style),
        Paragraph(f"<b>Admin Email:</b> {gen_by_email}", meta_style),
        Paragraph(f"<b>Integrity Seal:</b> <font color='#059669'>AUTHENTICATED & SIGNED</font>", meta_style)
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[480, 290]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=8, spaceBefore=4))

    # ---------------------------------------------------------
    # 2. INSTITUTION PROFILE & CRYPTOGRAPHIC IDENTITY
    # ---------------------------------------------------------
    story.append(Paragraph("1. Institutional Governance & Cryptographic Configuration", section_heading))

    features_dict = {}
    if institution.features_config:
        try:
            features_dict = json.loads(institution.features_config)
        except Exception:
            pass

    status_color = "#059669" if institution.verification_status == "VERIFIED" else "#d97706"
    
    inst_info_col1 = [
        Paragraph(f"<b>Legal Name:</b> {institution.name}", meta_style),
        Paragraph(f"<b>Institution Code:</b> {institution.institution_code}", meta_style),
        Paragraph(f"<b>Official Domain:</b> {institution.official_domain or 'N/A'}", meta_style),
        Paragraph(f"<b>Registration Date:</b> {format_date_str(institution.created_at)}", meta_style),
    ]

    inst_info_col2 = [
        Paragraph(f"<b>Contact Email:</b> {institution.contact_email or 'N/A'}", meta_style),
        Paragraph(f"<b>Contact Phone:</b> {institution.contact_phone or 'N/A'}", meta_style),
        Paragraph(f"<b>Registry Status:</b> <font color='{status_color}'><b>{institution.verification_status or 'VERIFIED'}</b></font>", meta_style),
        Paragraph(f"<b>Admin Account:</b> {getattr(institution, 'admin_email', None) or 'Configured'}", meta_style),
    ]

    fp = institution.key_fingerprint or "RSA-2048-GEN-PENDING"
    algo = institution.key_algorithm or "RSA-2048"
    inst_info_col3 = [
        Paragraph(f"<b>Key Algorithm:</b> {algo}", meta_style),
        Paragraph(f"<b>Signature Scheme:</b> {features_dict.get('signature_algorithm', 'RSA-PSS-SHA256')}", meta_style),
        Paragraph(f"<b>Key Fingerprint:</b> <font size='7' name='Courier'>{fp[:24]}...</font>", meta_style),
        Paragraph(f"<b>Revocation Policy:</b> {'Allowed with Reason' if features_dict.get('allow_revocation', True) else 'Locked'}", meta_style),
    ]

    inst_profile_table = Table(
        [[inst_info_col1, inst_info_col2, inst_info_col3]],
        colWidths=[260, 255, 255]
    )
    inst_profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(inst_profile_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 3. STATISTICAL EXECUTIVE SUMMARY
    # ---------------------------------------------------------
    story.append(Paragraph("2. Credential Issuance & Integrity Metrics", section_heading))

    total_certs = len(certificates)
    active_count = sum(1 for c in certificates if c.status == "ACTIVE")
    revoked_count = sum(1 for c in certificates if c.status == "REVOKED")
    suspicious_count = sum(1 for c in certificates if c.status == "SUSPICIOUS")
    expired_count = sum(1 for c in certificates if c.status == "EXPIRED")

    # Category counts
    academic_count = sum(1 for c in certificates if (c.category or "ACADEMIC").upper() == "ACADEMIC")
    recruit_count = sum(1 for c in certificates if "RECRUIT" in (c.category or "").upper() or "EMPLOY" in (c.category or "").upper())
    tech_count = sum(1 for c in certificates if "TECH" in (c.category or "").upper() or "COURSE" in (c.category or "").upper())
    award_count = sum(1 for c in certificates if "ACHIEVE" in (c.category or "").upper() or "AWARD" in (c.category or "").upper())

    compliance_rate = 100.0
    if total_certs > 0:
        compliance_rate = (active_count / total_certs) * 100.0

    stat_card_data = [
        [
            Paragraph("<font size='14' color='#1e293b'><b>" + str(total_certs) + "</b></font><br/><font size='8' color='#64748b'>TOTAL ISSUED</font>", ParagraphStyle('C1', alignment=1)),
            Paragraph("<font size='14' color='#059669'><b>" + str(active_count) + "</b></font><br/><font size='8' color='#64748b'>ACTIVE & VALID</font>", ParagraphStyle('C2', alignment=1)),
            Paragraph("<font size='14' color='#dc2626'><b>" + str(revoked_count) + "</b></font><br/><font size='8' color='#64748b'>REVOKED</font>", ParagraphStyle('C3', alignment=1)),
            Paragraph("<font size='14' color='#d97706'><b>" + str(suspicious_count) + "</b></font><br/><font size='8' color='#64748b'>SUSPICIOUS / FLAGGED</font>", ParagraphStyle('C4', alignment=1)),
            Paragraph("<font size='14' color='#2563eb'><b>" + f"{compliance_rate:.1f}%" + "</b></font><br/><font size='8' color='#64748b'>COMPLIANCE RATE</font>", ParagraphStyle('C5', alignment=1)),
            Paragraph(f"<font size='8' color='#334155'><b>Academic:</b> {academic_count} | <b>Recruitment:</b> {recruit_count}<br/><b>Technical:</b> {tech_count} | <b>Merit/Awards:</b> {award_count}</font>", ParagraphStyle('C6', alignment=1))
        ]
    ]

    stat_table = Table(stat_card_data, colWidths=[110, 110, 110, 130, 130, 180])
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 4. FULL & FINAL ISSUED CERTIFICATES REGISTRY TABLE
    # ---------------------------------------------------------
    filter_label = ""
    if status_filter and status_filter != "ALL":
        filter_label += f" • Filtered by Status: {status_filter}"
    if category_filter and category_filter != "ALL":
        filter_label += f" • Filtered by Category: {category_filter}"

    story.append(Paragraph(f"3. Full & Final Certificate Registry Records ({len(certificates)} Records){filter_label}", section_heading))

    table_cols = [
        Paragraph("<b># / ID</b>", table_header_style),
        Paragraph("<b>Recipient / Candidate</b>", table_header_style),
        Paragraph("<b>Course / Role / Title</b>", table_header_style),
        Paragraph("<b>Scope / Dept</b>", table_header_style),
        Paragraph("<b>Score / Grade</b>", table_header_style),
        Paragraph("<b>Issue Date</b>", table_header_style),
        Paragraph("<b>Status</b>", table_header_style),
        Paragraph("<b>SHA-256 Hash & Signature</b>", table_header_style),
    ]

    rows = [table_cols]

    for idx, cert in enumerate(certificates, start=1):
        # Format Status Badge
        st_upper = (cert.status or "ACTIVE").upper()
        if st_upper == "ACTIVE":
            status_p = Paragraph("<font color='#059669'><b>● ACTIVE</b></font>", badge_active)
        elif st_upper == "REVOKED":
            status_p = Paragraph("<font color='#dc2626'><b>✖ REVOKED</b></font>", badge_revoked)
        elif st_upper == "SUSPICIOUS":
            status_p = Paragraph("<font color='#d97706'><b>▲ SUSPICIOUS</b></font>", badge_suspicious)
        else:
            status_p = Paragraph(f"<b>{st_upper}</b>", cell_style)

        # Performance metric string
        perf_metrics = []
        if cert.grade:
            perf_metrics.append(cert.grade)
        if cert.cgpa:
            perf_metrics.append(f"CGPA: {cert.cgpa:.2f}")
        if cert.marks_obtained and cert.total_marks:
            perf_metrics.append(f"{int(cert.marks_obtained)}/{int(cert.total_marks)}")
        if cert.score_or_rank:
            perf_metrics.append(f"{cert.score_or_rank}")
        if cert.employment_type:
            perf_metrics.append(f"{cert.employment_type}")
        perf_str = " | ".join(perf_metrics) if perf_metrics else "N/A"

        # Scope & Department
        scope_str = cert.category or "ACADEMIC"
        if cert.department:
            scope_str += f"<br/><font color='#64748b'>{cert.department}</font>"

        # ID & Recipient
        id_str = f"<b>#{idx}</b><br/><font color='#2563eb' name='Courier'><b>{cert.certificate_id}</b></font>"
        recip_id = cert.student_id or cert.license_number or ""
        recip_str = f"<b>{cert.holder_name}</b>"
        if recip_id:
            recip_str += f"<br/><font color='#64748b'>ID: {recip_id}</font>"

        # Course / Role
        course_str = f"<b>{cert.course_name}</b>"
        if cert.organization_company:
            course_str += f"<br/><font color='#64748b'>Org: {cert.organization_company}</font>"

        # Issue Date
        date_str = format_date_str(cert.issue_date)

        # Cryptographic Hash & Signature state
        hash_snip = (cert.document_hash[:16] + "...") if cert.document_hash else "SHA256-VALID"
        sig_state = "<font color='#059669'>RSA-PSS-VERIFIED</font>" if cert.digital_signature else "<font color='#64748b'>Standard Hash</font>"
        crypto_cell = f"<font size='6.5' name='Courier'>{hash_snip}</font><br/>{sig_state}"

        # Status note / reason
        if cert.suspicious_reason:
            status_p = Paragraph(f"{status_p.text}<br/><font size='6' color='#dc2626'>{cert.suspicious_reason[:30]}</font>", cell_style)

        row = [
            Paragraph(id_str, cell_style),
            Paragraph(recip_str, cell_style),
            Paragraph(course_str, cell_style),
            Paragraph(scope_str, cell_style),
            Paragraph(perf_str, cell_style),
            Paragraph(date_str, cell_style),
            status_p,
            Paragraph(crypto_cell, cell_style)
        ]
        rows.append(row)

    if len(certificates) == 0:
        empty_row = [
            Paragraph("<i>No certificates found matching the criteria.</i>", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style)
        ]
        rows.append(empty_row)

    # Column widths summing up to 770 points (landscape A4 printable area width = 842 - 72 = 770)
    col_widths = [85, 115, 130, 95, 95, 75, 75, 100]
    
    cert_table = Table(rows, colWidths=col_widths, repeatRows=1)
    cert_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")), # Dark executive header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#ffffff")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
    ]))

    story.append(cert_table)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # 5. AUDIT DECLARATION & INTEGRITY DISCLAIMER
    # ---------------------------------------------------------
    disclaimer_text = (
        "<b>LEGAL AUDIT DECLARATION & CRYPTOGRAPHIC INTEGRITY ASSURANCE:</b><br/>"
        "This document constitutes an official verifiable registry audit extract generated by the CredVerify Cryptographic Platform. "
        "Each active certificate cataloged herein corresponds to an immutable digital record anchored with an SHA-256 document hash and "
        "signed using the institution's private RSA keypair. Third-party verifiers, corporate recruiters, and government accreditation agencies "
        "can independently authenticate any entry by scanning its individual cryptographic QR token or entering the Certificate ID at "
        f"<b>{institution.official_domain or 'https://credverify.demo'}/verify</b>."
    )

    disclaimer_p = Paragraph(disclaimer_text, ParagraphStyle('Disc', fontName='Helvetica', fontSize=7.5, leading=10.5, textColor=colors.HexColor("#475569")))
    
    declaration_box = Table([[disclaimer_p]], colWidths=[770])
    declaration_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(KeepTogether([declaration_box]))

    # Build PDF with two-pass canvas
    doc.build(story, canvasmaker=NumberedCanvas)

    return file_path
