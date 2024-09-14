"""Host type definitions."""


class SecretString:
    """Secret string.

    - Access a secret value only using explicit reveal() method
    - Erase secret value from memory before object destruction
    """

    def __init__(self, value: str) -> None:
        """Initialize."""
        self.__value = bytearray(value, "utf-8")

    def reveal(self) -> str:
        """Return the actual secret value."""
        return self.__value.decode("utf-8")

    def erase(self) -> None:
        """Erase secret value from memory."""
        for i in range(len(self.__value)):
            self.__value[i] = 0  # Overwrite each byte with null byte

    def __str__(self) -> str:
        """Return masked representation."""
        return "******"

    def __repr__(self) -> str:
        """Return masked representation."""
        return "'******'"

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if isinstance(other, SecretString):
            return self.__value == other.__value
        return False

    def __hash__(self) -> int:
        """Return object hash."""
        return hash(self.__value.decode("utf-8"))

    def __del__(self):
        """Erase value from memory before object is destroyed."""
        self.erase()
