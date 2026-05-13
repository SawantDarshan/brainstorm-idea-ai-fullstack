import os
import json
import base64
import logging

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Try to initialize Firebase Admin SDK (optional)
_firebase_available = False
try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth

    if not firebase_admin._apps:
        firebase_creds_b64 = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_creds_b64:
            cred_dict = json.loads(base64.b64decode(firebase_creds_b64))
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            _firebase_available = True
        else:
            _cred_path = os.path.join(os.path.dirname(__file__), "..", "config", "firebase-service-account.json")
            if os.path.exists(_cred_path):
                cred = credentials.Certificate(_cred_path)
                firebase_admin.initialize_app(cred)
                _firebase_available = True
            else:
                logger.warning("Firebase credentials not found. Auth is disabled.")
    else:
        _firebase_available = True
except Exception as e:
    logger.warning(f"Firebase init failed: {e}. Auth is disabled.")

# Bearer token scheme
security = HTTPBearer(auto_error=False)


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    if not _firebase_available:
        return {"uid": "anonymous", "email": "anonymous@local"}
    try:
        from firebase_admin import auth as firebase_auth
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency — verifies Firebase ID token. If Firebase is not configured, allows anonymous access."""
    if not _firebase_available:
        return {"uid": "anonymous", "email": "anonymous@local"}
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_firebase_token(credentials.credentials)