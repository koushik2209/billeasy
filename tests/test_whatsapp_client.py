"""Tests for Meta WhatsApp Cloud API client (no network calls)."""

import os

from whatsapp_client import (
    digits_only,
    normalize_whatsapp_sender,
    parse_meta_webhook_payload,
)


def test_digits_only_strips_formatting():
    assert digits_only("whatsapp:+919876543210") == "919876543210"
    assert digits_only("+1 415 555 1212") == "14155551212"


def test_normalize_whatsapp_sender_meta_format():
    assert normalize_whatsapp_sender("919876543210") == "whatsapp:+919876543210"


def test_parse_meta_webhook_payload_extracts_text():
    body = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "type": "text",
                                    "text": {"body": "hello bill"},
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }
    msgs = parse_meta_webhook_payload(body)
    assert len(msgs) == 1
    assert msgs[0]["text"] == "hello bill"
    assert msgs[0]["from"] == "whatsapp:+919876543210"


def test_parse_meta_webhook_skips_non_text():
    body = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": "91x", "type": "image", "image": {"id": "1"}}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    assert parse_meta_webhook_payload(body) == []


def test_meta_webhook_get_verification():
    """GET /webhook returns hub.challenge when verify_token matches VERIFY_TOKEN."""
    from whatsapp_webhook import app

    client = app.test_client()
    resp = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": os.environ.get("VERIFY_TOKEN", "test-verify-token"),
            "hub.challenge": "CHALLENGE_ACCEPTED",
        },
    )
    assert resp.status_code == 200
    assert resp.data.decode() == "CHALLENGE_ACCEPTED"

    resp_bad = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "x",
        },
    )
    assert resp_bad.status_code == 403
