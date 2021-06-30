import pytest

pytest.register_assert_rewrite(f"{__package__}._helpers")
pytest.register_assert_rewrite(f"{__package__}._discord_helpers")
