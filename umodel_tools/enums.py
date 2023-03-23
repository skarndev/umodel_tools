import enum


class SpecialBlendingMode(enum.Enum):
    """List of special blenbing modes that require additional node generation.
    """

    #: Final color = Source color + Dest color.
    Add = enum.auto()

    #: Final color = Source color x Dest color.
    Mod = enum.auto()
