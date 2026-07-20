import os
import requests
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

# ── Simple in-memory cache so we don't call Clerk on every request ────
_jwks_cache = None

def _get_jwks(jwks_url: str) -> dict:
    """Fetch Clerk's public keys (cached in memory)."""
    global _jwks_cache
    if _jwks_cache is None:
        try:
            resp = requests.get(jwks_url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not fetch Clerk public keys: {e}"
            )
    return _jwks_cache

# ── Reads 'Authorization: Bearer <token>' from request headers ────────
security = HTTPBearer()

def verify_clerk_token(token: str) -> dict:
    """
    Verifies a Clerk session JWT.
    1. Decodes the token header (without verifying) to get the key ID
    2. Fetches Clerk's public keys (JWKS) using the token's own issuer URL
    3. Verifies the token signature using the matching public key
    Returns the decoded payload (contains 'sub' = Clerk user ID).
    """
    global _jwks_cache

    try:
        # Step 1: Read the token header to get key ID (kid)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # Step 2: Read the token claims (unverified) to get the issuer URL
        unverified_claims = jwt.get_unverified_claims(token)
        issuer = unverified_claims.get("iss")
        if not issuer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing issuer claim"
            )

        # Step 3: Build the JWKS URL from the issuer
        jwks_url = f"{issuer}/.well-known/jwks.json"

        # Step 4: Fetch public keys and find the matching one
        jwks = _get_jwks(jwks_url)
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)

        # If key not found, the keys may have rotated — clear cache and retry
        if key is None:
            _jwks_cache = None
            jwks = _get_jwks(jwks_url)
            key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)

        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signing key not found in Clerk JWKS"
            )

        # Step 5: Verify and decode the token using the public key
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Clerk tokens don't always set 'aud'
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


async def get_current_user_clerk(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency — drop-in replacement for old get_current_user.
    Usage in a router:
        current_user = Depends(get_current_user_clerk)
    Returns the decoded Clerk token payload.
    'current_user["sub"]' gives you the Clerk user ID.
    """
    return verify_clerk_token(credentials.credentials)
