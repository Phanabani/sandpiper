__all__ = ('qualified',)


def qualified(parent: str, name: str) -> str:
    return (parent + '.' if parent else '') + name
