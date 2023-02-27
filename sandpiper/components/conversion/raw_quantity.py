from attr import define


@define
class RawQuantity:
    quantity: str
    suffix: str
