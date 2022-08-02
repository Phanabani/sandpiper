import sqlalchemy as sa
from sqlalchemy import Column

from .base import Base


class SandpiperMeta(Base):
    __tablename__ = 'sandpiper_meta'
    __mapper_args__ = {'eager_defaults': True}

    # Not necessarily required, but the ORM wants a primary key column, so this
    # is just a dummy column for now
    id = Column(sa.Integer, primary_key=True)
    version = Column(sa.String)
