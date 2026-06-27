from ghostliness.auth import Authenticator, offline_uuid


def test_offline_uuid_is_stable():
    assert offline_uuid("Steve") == offline_uuid("Steve")
    assert offline_uuid("Steve") != offline_uuid("Alex")


async def test_both_mode_falls_back_to_offline_until_online_backend_exists():
    profile = await Authenticator("both").authenticate("Steve")
    assert profile.username == "Steve"
    assert profile.online is False
