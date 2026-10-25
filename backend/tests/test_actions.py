from app.schemas import ActionDraftRequest
from app.services.actions import draft_action


def test_action_drafts_are_editable_templates_in_supported_languages():
    for language in ("en", "hi", "kn"):
        result = draft_action(
            ActionDraftRequest(
                action="hotel_late_checkin",
                language=language,
                provider_name="Coastal Hotel",
                origin="Mangaluru",
                destination="Udupi",
            )
        )
        assert result["provider_name"] == "Coastal Hotel"
        assert result["requires_user_review"] is True
        assert result["sent"] is False
        assert result["source"] == "StrandedPool editable template"
        assert "Mangaluru" in result["content"]
        assert "Udupi" in result["content"]


def test_refund_template_does_not_claim_eligibility():
    result = draft_action(
        ActionDraftRequest(
            action="refund_inquiry",
            provider_name="Rail operator",
            origin="Mangaluru",
            destination="Udupi",
        )
    )
    assert "eligibility" in result["content"]
