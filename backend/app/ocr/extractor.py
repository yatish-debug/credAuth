import cv2
import pytesseract
from PIL import Image
import os
import re

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using Pytesseract.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except pytesseract.TesseractNotFoundError:
        return "OCR_UNAVAILABLE: Tesseract is not installed on this system."
    except Exception as e:
        return f"OCR_ERROR: {str(e)}"

def extract_certificate_data(file_path: str) -> dict:
    """
    Process the uploaded file and extract fields including ID, Name, CGPA, Grade, PRN, etc.
    """
    try:
        import pdfplumber
        
        if file_path.lower().endswith('.pdf'):
            extracted_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() + "\n"
        else:
            extracted_text = extract_text_from_image(file_path)
            
    except ImportError:
        extracted_text = extract_text_from_image(file_path)
        
    data = {
        "certificate_id": None,
        "holder_name": None,
        "student_id": None,
        "course_name": None,
        "cgpa": None,
        "grade": None,
        "raw_text": extracted_text
    }
    
    # 1. Certificate ID (CV-2026-XXXXXXXX)
    cert_id_match = re.search(r'(CV-\d{4}-[A-Z0-9]+)', extracted_text, re.IGNORECASE)
    if cert_id_match:
        data["certificate_id"] = cert_id_match.group(1).upper()
        
    # 2. PRN / Student ID
    prn_match = re.search(r'(?:PRN|Roll\s*No|Student\s*ID)[:\s]+([A-Z0-9\-]+)', extracted_text, re.IGNORECASE)
    if prn_match:
        data["student_id"] = prn_match.group(1).strip()
        
    # 3. CGPA (e.g. CGPA: 9.85 / CGPA: 8.92/10.0)
    cgpa_match = re.search(r'CGPA[:\s]+(\d+(?:\.\d+)?)', extracted_text, re.IGNORECASE)
    if cgpa_match:
        try:
            data["cgpa"] = float(cgpa_match.group(1))
        except ValueError:
            pass

    # 4. Grade (e.g. Grade: Distinction / Grade: A+)
    grade_match = re.search(r'Grade[:\s]+([A-Za-z0-9\+\s]+?)(?=\s*•|\s*\||\s*CGPA|\s*\n|$)', extracted_text, re.IGNORECASE)
    if grade_match:
        data["grade"] = grade_match.group(1).strip()
        
    return data
