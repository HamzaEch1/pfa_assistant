# api/core/two_factor.py
import pyotp
import qrcode
import base64
import io
import logging
from typing import Dict, Tuple

from ..schemas.user import TwoFactorSetupResponse

logger = logging.getLogger(__name__)

def generate_totp_secret() -> str:
    """Generate a random secret for TOTP"""
    return pyotp.random_base32()

def generate_totp_uri(secret: str, username: str, issuer: str = "Banque Populaire") -> str:
    """Generate the OTP auth URI for the QR code"""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)

def generate_qr_code(uri: str) -> str:
    """Generate QR code image and return as base64 string"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save image to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)  # Reset buffer position to beginning
        
        # Convert to base64 string
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Validate non-empty result
        if not qr_code_base64:
            raise ValueError("Generated QR code is empty")
            
        return qr_code_base64
    except Exception as e:
        logger.error(f"Error generating QR code: {e}", exc_info=True)
        # Return a placeholder or fallback empty string
        return ""

def setup_2fa(username: str) -> TwoFactorSetupResponse:
    """Set up 2FA for a user, return secret and QR code"""
    try:
        # Generate secret
        secret = generate_totp_secret()
        
        # Generate provisioning URI
        uri = generate_totp_uri(secret, username)
        
        # Generate QR code
        qr_code = generate_qr_code(uri)
        
        # Log success or failure
        if qr_code:
            logger.info(f"Successfully generated QR code for user {username}")
        else:
            logger.warning(f"QR code generation failed for user {username}, but continuing with setup")
        
        response = TwoFactorSetupResponse(
            secret=secret,
            provisioning_uri=uri,
            qr_code=qr_code
        )
        
        # Log response structure for debugging
        logger.debug(f"2FA setup response: secret length={len(secret)}, uri length={len(uri)}, qr_code length={len(qr_code) if qr_code else 0}")
        
        return response
    except Exception as e:
        logger.error(f"Error setting up 2FA for {username}: {e}", exc_info=True)
        raise

def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against the secret"""
    if not secret or not code:
        return False
    
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    except Exception as e:
        logger.error(f"Error verifying TOTP: {e}", exc_info=True)
        return False 