import pytest

for helper in ('discord', 'misc', 'mocking'):
    pytest.register_assert_rewrite(f'{__spec__.parent}.helpers.{helper}')
