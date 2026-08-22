import os
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

def generate_certificate_pdf(
    certificate_id: str,
    holder_name: str,
    course_name: str,
    institution_name: str,
    issue_date: str,
    qr_image_path: str,
    category: str = "ACADEMIC",
    student_id: str = None,
    department: str = None,
    academic_year: str = None,
    marks_obtained: float = None,
    total_marks: float = None,
    percentage: float = None,
    cgpa: float = None,
    grade: str = None,
    remarks: str = None,
    role_designation: str = None,
    organization_company: str = None,
    skills_acquired: str = None,
    employment_type: str = None,
    license_number: str = None,
    score_or_rank: str = None
) -> str:
    """
    Generates a multi-domain professional credential PDF for Academic, Recruitment, Technical Courses, and Awards.
    """
    os.makedirs(os.path.join("storage", "certificates"), exist_ok=True)
    file_name = f"{certificate_id}.pdf"
    file_path = os.path.join("storage", "certificates", file_name)
    
    c = canvas.Canvas(file_path, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # 1. THEME SELECTION BASED ON DOMAIN CATEGORY
    cat_upper = (category or "ACADEMIC").upper()
    
    if "RECRUIT" in cat_upper or "EMPLOY" in cat_upper:
        # Corporate & Recruitment Theme: Deep Navy & Bronze/Gold
        bg_color = colors.HexColor("#09101d") # Dark corporate blue
        border_outer = colors.HexColor("#2563eb") # Royal blue
        border_inner = colors.HexColor("#f59e0b") # Amber/Gold
        accent_color = colors.HexColor("#60a5fa")
        ribbon_bg = colors.HexColor("#1e293b")
        title_text = "OFFICIAL EMPLOYMENT & EXPERIENCE VERIFICATION"
        cert_type_header = "CORPORATE CREDENTIAL REGISTRY"
    elif "TECH" in cat_upper or "COURSE" in cat_upper:
        # High-Tech & Technical Course Theme: Cyber Dark Slate & Neon Cyan
        bg_color = colors.HexColor("#030712") # Ultra dark slate
        border_outer = colors.HexColor("#06b6d4") # Cyan 500
        border_inner = colors.HexColor("#10b981") # Emerald
        accent_color = colors.HexColor("#22d3ee")
        ribbon_bg = colors.HexColor("#082f49")
        title_text = "PROFESSIONAL TECHNICAL CERTIFICATION"
        cert_type_header = "GLOBAL TECHNICAL SKILLS & EXAM REGISTRY"
    elif "ACHIEVE" in cat_upper or "AWARD" in cat_upper:
        # Hackathons & Merit Awards Theme: Royal Purple & Gold
        bg_color = colors.HexColor("#13091f")
        border_outer = colors.HexColor("#a855f7") # Purple
        border_inner = colors.HexColor("#fbbf24") # Warm Gold
        accent_color = colors.HexColor("#c084fc")
        ribbon_bg = colors.HexColor("#2e1065")
        title_text = "CERTIFICATE OF MERIT & EXCELLENCE"
        cert_type_header = "ACHIEVEMENT & COMPETITION AWARDS"
    else:
        # Academic & Degree Theme: Indigo & Sky Blue
        bg_color = colors.HexColor("#0f172a")
        border_outer = colors.HexColor("#4f46e5")
        border_inner = colors.HexColor("#38bdf8")
        accent_color = colors.HexColor("#818cf8")
        ribbon_bg = colors.HexColor("#1e1b4b")
        title_text = "ACADEMIC DEGREE & DIPLOMA CREDENTIAL"
        cert_type_header = "ACADEMIC & HIGHER EDUCATION REGISTRY"
        
    # Background
    c.setFillColor(bg_color)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Outer Luxury Double Border
    c.setStrokeColor(border_outer)
    c.setLineWidth(4)
    c.rect(0.4 * inch, 0.4 * inch, width - 0.8 * inch, height - 0.8 * inch)
    
    c.setStrokeColor(border_inner)
    c.setLineWidth(1)
    c.rect(0.46 * inch, 0.46 * inch, width - 0.92 * inch, height - 0.92 * inch)
    
    # Watermark
    c.saveState()
    c.setFont("Helvetica-Bold", 75)
    c.setFillColor(colors.HexColor("#1e293b"))
    c.translate(width/2, height/2)
    c.rotate(32)
    watermark_label = "OFFICIALLY AUTHENTICATED"
    c.drawCentredString(0, 0, watermark_label)
    c.restoreState()
    
    # Header: Organization / Institution / Company Name
    org_display = organization_company or institution_name or "CREDVERIFY PLATFORM"
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#ffffff"))
    c.drawCentredString(width/2, height - 1.15 * inch, org_display.upper())
    
    # Subheader / Registry Type
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawCentredString(width/2, height - 1.45 * inch, cert_type_header)
    
    # Main Certificate Title
    c.setFont("Helvetica-Bold", 19)
    c.setFillColor(border_inner)
    c.drawCentredString(width/2, height - 1.95 * inch, title_text)
    
    # Presentation Line
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#cbd5e1"))
    if "RECRUIT" in cat_upper:
        c.drawCentredString(width/2, height - 2.45 * inch, "This credential officially confirms that")
    elif "TECH" in cat_upper:
        c.drawCentredString(width/2, height - 2.45 * inch, "This is to certify that the professional")
    else:
        c.drawCentredString(width/2, height - 2.45 * inch, "This is to certify that")
    
    # Recipient Name
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#ffffff"))
    c.drawCentredString(width/2, height - 2.95 * inch, holder_name)
    
    # Identification Tag (PRN / Employee ID / Candidate ID)
    id_label = "Employee / Candidate ID" if "RECRUIT" in cat_upper else "Student PRN / Roll No" if "ACADEMIC" in cat_upper else "Credential / License ID"
    ident_val = student_id or license_number
    if ident_val:
        c.setFont("Helvetica", 11)
        c.setFillColor(accent_color)
        c.drawCentredString(width/2, height - 3.25 * inch, f"{id_label}: {ident_val}")
        
    # Program / Role / Certification Context Line
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#e2e8f0"))
    
    if "RECRUIT" in cat_upper:
        role_str = role_designation or course_name
        emp_type_str = f" as {employment_type}" if employment_type else ""
        dept_str = f" in {department}" if department else ""
        c.drawCentredString(width/2, height - 3.65 * inch, f"has served as {role_str}{emp_type_str}{dept_str}")
    elif "TECH" in cat_upper:
        cert_name_str = course_name or role_designation
        c.drawCentredString(width/2, height - 3.65 * inch, f"has successfully passed and mastered the technical certification for {cert_name_str}")
    else:
        dept_str = f" in Department of {department}" if department else ""
        c.drawCentredString(width/2, height - 3.65 * inch, f"has fulfilled all curriculum requirements for {course_name}{dept_str}")
        
    # PERFORMANCE / SKILLS / METRICS RIBBON (Horizontal Badge Bar)
    badge_items = []
    
    if "RECRUIT" in cat_upper:
        if employment_type:
            badge_items.append(f"Type: {employment_type}")
        if academic_year:
            badge_items.append(f"Tenure: {academic_year}")
        if grade or score_or_rank:
            badge_items.append(f"Rating: {grade or score_or_rank}")
        if skills_acquired:
            badge_items.append(f"Competencies: {skills_acquired[:40]}")
    elif "TECH" in cat_upper:
        if license_number:
            badge_items.append(f"Exam: {license_number}")
        if score_or_rank:
            badge_items.append(f"Score: {score_or_rank}")
        if skills_acquired:
            badge_items.append(f"Tech Stack: {skills_acquired[:45]}")
        if grade:
            badge_items.append(f"Proficiency: {grade}")
    else:
        # Academic metrics
        if grade:
            badge_items.append(f"Grade: {grade}")
        if cgpa:
            badge_items.append(f"CGPA: {cgpa:.2f}/10.0")
        if marks_obtained and total_marks:
            pct_val = percentage if percentage else (marks_obtained / total_marks * 100)
            badge_items.append(f"Marks: {int(marks_obtained)}/{int(total_marks)} ({pct_val:.1f}%)")
        if academic_year:
            badge_items.append(f"Session: {academic_year}")
            
    if badge_items:
        ribbon_text = "   •   ".join(badge_items)
        c.setFillColor(ribbon_bg)
        c.roundRect(0.9 * inch, height - 4.35 * inch, width - 1.8 * inch, 0.42 * inch, 6, fill=1, stroke=0)
        c.setStrokeColor(border_outer)
        c.setLineWidth(1)
        c.roundRect(0.9 * inch, height - 4.35 * inch, width - 1.8 * inch, 0.42 * inch, 6, fill=0, stroke=1)
        
        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColor(accent_color)
        c.drawCentredString(width/2, height - 4.22 * inch, ribbon_text)

    # Bottom Left: Cryptographic Metadata
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.drawString(0.9 * inch, 1.6 * inch, "CRYPTOGRAPHIC REGISTRY VALIDATION:")
    
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#cbd5e1"))
    c.drawString(0.9 * inch, 1.38 * inch, f"Credential ID:   {certificate_id}")
    c.drawString(0.9 * inch, 1.18 * inch, f"Date of Issue:   {issue_date}")
    c.drawString(0.9 * inch, 0.98 * inch, f"Domain Scope:    {cat_upper} (Asymmetric RSA-2048 & SHA-256 Validated)")
    if remarks:
        c.drawString(0.9 * inch, 0.78 * inch, f"Official Note:   {remarks}")
    
    # Bottom Right: QR Code & Verification Stamp
    if os.path.exists(qr_image_path):
        qr_img = ImageReader(qr_image_path)
        c.drawImage(qr_img, width - 2.5 * inch, 0.75 * inch, width=1.5 * inch, height=1.5 * inch)
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(border_inner)
        c.drawCentredString(width - 1.75 * inch, 0.60 * inch, "SCAN TO VERIFY INTEGRITY")
        
    c.showPage()
    c.save()
    
    return file_path
