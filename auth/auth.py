import os
import json
import base64

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    # Option 1: FIREBASE_CREDENTIALS env var (base64-encoded JSON) — for Vercel/cloud
    firebase_creds_b64 = os.environ.get("FIREBASE_CREDENTIALS")
    if firebase_creds_b64:
        cred_dict = json.loads(base64.b64decode(firebase_creds_b64))
        cred = credentials.Certificate(cred_dict)
    else:
        # Option 2: Local file
        _cred_path = os.path.join(os.path.dirname(__file__), "..", "config", "firebase-service-account.json")
        cred = credentials.Certificate(_cred_path)
    firebase_admin.initialize_app(cred)

# Bearer token scheme
security = HTTPBearer()


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency — verifies Firebase ID token from Authorization header."""
    return verify_firebase_token(credentials.credentials)