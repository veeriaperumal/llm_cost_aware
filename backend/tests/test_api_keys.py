import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import encrypt_secret, decrypt_secret, mask_key
from app.services.key_service import KeyService
from app.models.schemas import SaveAPIKeyRequest, ChatRequest
from app.graph.cascading_router import CascadingRouter
from app.database import init_db


@pytest.mark.asyncio
async def test_encryption_decryption_and_masking():
    raw_key = "AIzaSyD-1234567890abcdefghijklmnopqrstuvw"
    encrypted = encrypt_secret(raw_key)
    assert encrypted != raw_key
    assert len(encrypted) > 20

    decrypted = decrypt_secret(encrypted)
    assert decrypted == raw_key

    hint = mask_key(raw_key)
    assert hint.startswith("AIzaSy")
    assert hint.endswith("tuvw")
    assert "..." in hint
    assert raw_key not in hint


@pytest.mark.asyncio
async def test_key_service_crud():
    await init_db()
    test_user = "test_user_pytest_123"
    gemini_raw = "AIzaSyMockKeyForGeminiValidation999"
    groq_raw = "gsk_MockKeyForGroqValidation888"

    # 1. Upsert Gemini Key
    res_gem = await KeyService.upsert_user_key(test_user, "gemini", gemini_raw)
    assert res_gem["user_id"] == test_user
    assert res_gem["provider_name"] == "gemini"
    assert res_gem["key_hint"] == mask_key(gemini_raw)

    # 2. Upsert Groq Key
    res_groq = await KeyService.upsert_user_key(test_user, "groq", groq_raw)
    assert res_groq["provider_name"] == "groq"

    # 3. Retrieve all keys (masked)
    all_keys = await KeyService.get_user_keys(test_user)
    assert len(all_keys) == 2
    providers = [k["provider_name"] for k in all_keys]
    assert "gemini" in providers
    assert "groq" in providers

    # 4. Decrypt single key
    decrypted_gemini = await KeyService.get_decrypted_user_key(test_user, "gemini")
    assert decrypted_gemini == gemini_raw

    # 5. Decrypt all keys dict
    all_decrypted = await KeyService.get_all_decrypted_user_keys(test_user)
    assert all_decrypted["gemini"] == gemini_raw
    assert all_decrypted["groq"] == groq_raw

    # 6. Delete key
    deleted = await KeyService.delete_user_key(test_user, "gemini")
    assert deleted is True

    keys_after_delete = await KeyService.get_user_keys(test_user)
    assert len(keys_after_delete) == 1
    assert keys_after_delete[0]["provider_name"] == "groq"

    # Cleanup
    await KeyService.delete_user_key(test_user, "groq")


@pytest.mark.asyncio
async def test_router_with_user_context():
    await init_db()
    test_user = "test_user_router_456"
    
    # Run query with user_id header / field
    request = ChatRequest(
        prompt="Explain reactive state management in modern architectures.",
        provider="mock",
        user_id=test_user,
    )
    response = await CascadingRouter.process_query(request)
    assert response.final_answer is not None
    assert len(response.final_answer) > 0
    assert response.cost_breakdown is not None
