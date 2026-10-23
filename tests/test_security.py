import hashlib
import hmac
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

from utils.security import validate_telegram_init_data


def _sign(bot_token: str, fields: dict[str, str]) -> str:
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()


def test_init_data_ok():
    fields = {"auth_date": "1000000000", "user": '{"id":1,"username":"a"}'}
    fields["hash"] = _sign("123456:TESTTOKEN", {k: v for k, v in fields.items() if k != "hash"})
    parsed = validate_telegram_init_data(urlencode(fields), "123456:TESTTOKEN", max_age_seconds=10**12)
    assert parsed["user"]["id"] == 1


def test_init_data_bad_hash():
    with pytest.raises(HTTPException):
        validate_telegram_init_data("auth_date=1&hash=deadbeef&user=%7B%22id%22%3A1%7D", "123456:TESTTOKEN")
