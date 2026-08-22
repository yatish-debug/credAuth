import qrcode
import os
from app.core.config import settings

def generate_qr_code(qr_token: str, certificate_id: str) -> str:
    """
    Generates a high-resolution QR code image that points to the verification URL and saves it.
    Returns the file path.
    """
    os.makedirs(os.path.join("storage", "qr"), exist_ok=True)
    verify_url = f"{settings.FRONTEND_URL}/verify/{qr_token}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save both with token and certificate ID for 100% resolution compatibility
    token_file_path = os.path.join("storage", "qr", f"{qr_token}.png")
    cert_file_path = os.path.join("storage", "qr", f"{certificate_id}_qr.png")
    
    img.save(token_file_path)
    img.save(cert_file_path)
    
    return token_file_path
