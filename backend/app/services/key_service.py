import httpx
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import select, delete
from app.database import async_session
from app.models.db_models import UserAPIKey
from app.core.security import encrypt_secret, decrypt_secret, mask_key
from config.settings import settings


class KeyService:
    @staticmethod
    async def get_user_keys(user_id: str) -> List[Dict[str, Any]]:
        """Fetch all configured keys for a given user ID (masked)."""
        if not user_id:
            return []
        async with async_session() as session:
            stmt = select(UserAPIKey).where(UserAPIKey.user_id == user_id).order_by(UserAPIKey.provider_name)
            result = await session.execute(stmt)
            keys = result.scalars().all()
            return [
                {
                    "id": k.id,
                    "user_id": k.user_id,
                    "provider_name": k.provider_name,
                    "key_hint": k.key_hint,
                    "is_valid": k.is_valid,
                    "last_validated_at": k.last_validated_at.isoformat() if k.last_validated_at else None,
                    "created_at": k.created_at.isoformat() if k.created_at else None,
                    "updated_at": k.updated_at.isoformat() if k.updated_at else None,
                }
                for k in keys
            ]

    @staticmethod
    async def get_decrypted_user_key(user_id: str, provider: str) -> Optional[str]:
        """Fetch and decrypt the active key for a user and provider. Returns None if not found or empty."""
        if not user_id or not provider:
            return None
        provider_clean = provider.lower().strip()
        async with async_session() as session:
            stmt = select(UserAPIKey).where(
                UserAPIKey.user_id == user_id,
                UserAPIKey.provider_name == provider_clean,
            ).limit(1)
            result = await session.execute(stmt)
            record = result.scalars().first()
            if record and record.encrypted_key:
                raw_key = decrypt_secret(record.encrypted_key)
                if raw_key:
                    return raw_key
        return None

    @staticmethod
    async def get_all_decrypted_user_keys(user_id: str) -> Dict[str, str]:
        """Returns dict of {provider_name: raw_key} for all configured keys of this user."""
        if not user_id:
            return {}
        async with async_session() as session:
            stmt = select(UserAPIKey).where(UserAPIKey.user_id == user_id)
            result = await session.execute(stmt)
            records = result.scalars().all()
            keys_dict = {}
            for r in records:
                if r.encrypted_key:
                    raw = decrypt_secret(r.encrypted_key)
                    if raw:
                        keys_dict[r.provider_name.lower().strip()] = raw
            return keys_dict

    @staticmethod
    async def upsert_user_key(user_id: str, provider: str, raw_key: str, is_valid: bool = True) -> Dict[str, Any]:
        """Save or update an API key for a user."""
        if not user_id or not provider or not raw_key:
            raise ValueError("user_id, provider, and raw_key are required.")

        provider_clean = provider.lower().strip()
        raw_key_clean = raw_key.strip()
        encrypted = encrypt_secret(raw_key_clean)
        hint = mask_key(raw_key_clean)
        now = datetime.now(timezone.utc)

        async with async_session() as session:
            stmt = select(UserAPIKey).where(
                UserAPIKey.user_id == user_id,
                UserAPIKey.provider_name == provider_clean,
            ).limit(1)
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                existing.encrypted_key = encrypted
                existing.key_hint = hint
                existing.is_valid = is_valid
                existing.last_validated_at = now
                existing.updated_at = now
                await session.commit()
                await session.refresh(existing)
                record = existing
            else:
                record = UserAPIKey(
                    user_id=user_id,
                    provider_name=provider_clean,
                    encrypted_key=encrypted,
                    key_hint=hint,
                    is_valid=is_valid,
                    last_validated_at=now,
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)

            return {
                "id": record.id,
                "user_id": record.user_id,
                "provider_name": record.provider_name,
                "key_hint": record.key_hint,
                "is_valid": record.is_valid,
                "last_validated_at": record.last_validated_at.isoformat() if record.last_validated_at else None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            }

    @staticmethod
    async def delete_user_key(user_id: str, provider: str) -> bool:
        """Delete a saved API key for a user."""
        if not user_id or not provider:
            return False
        provider_clean = provider.lower().strip()
        async with async_session() as session:
            stmt = delete(UserAPIKey).where(
                UserAPIKey.user_id == user_id,
                UserAPIKey.provider_name == provider_clean,
            )
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    @staticmethod
    async def validate_provider_key(provider: str, raw_key: str) -> Tuple[bool, str]:
        """Perform a quick live ping to verify if the provided API key is valid for the given provider."""
        p = provider.lower().strip()
        k = raw_key.strip()
        if not k:
            return False, "API key cannot be empty"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                if p == "gemini":
                    # Ping models.list or lightweight generateContent
                    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={k}"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return True, "Valid Google Gemini API key"
                    error_msg = resp.json().get("error", {}).get("message", f"Gemini error ({resp.status_code})")
                    return False, error_msg

                elif p == "groq":
                    # Ping models list
                    url = "https://api.groq.com/openai/v1/models"
                    headers = {"Authorization": f"Bearer {k}"}
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        return True, "Valid Groq Cloud API key"
                    error_msg = resp.json().get("error", {}).get("message", f"Groq error ({resp.status_code})")
                    return False, error_msg

                elif p in ["anthropic", "claude"]:
                    # Anthropic doesn't have a simple GET /models without beta header, let's test a 1-token message or check /v1/messages
                    url = "https://api.anthropic.com/v1/messages"
                    headers = {
                        "x-api-key": k,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }
                    payload = {
                        "model": "claude-3-5-haiku-20241022",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "ping"}]
                    }
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code in [200, 429]:  # 429 means valid key but rate limited
                        return True, "Valid Anthropic Claude API key"
                    error_msg = resp.json().get("error", {}).get("message", f"Anthropic error ({resp.status_code})")
                    return False, error_msg

                elif p == "openai":
                    url = "https://api.openai.com/v1/models"
                    headers = {"Authorization": f"Bearer {k}"}
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        return True, "Valid OpenAI API key"
                    error_msg = resp.json().get("error", {}).get("message", f"OpenAI error ({resp.status_code})")
                    return False, error_msg

                elif p == "mistral":
                    url = "https://api.mistral.ai/v1/models"
                    headers = {"Authorization": f"Bearer {k}"}
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        return True, "Valid Mistral AI API key"
                    error_msg = resp.json().get("message", f"Mistral error ({resp.status_code})")
                    return False, error_msg

                else:
                    return False, f"Unknown provider '{provider}'"
            except Exception as e:
                return False, f"Connection error: {str(e)}"
