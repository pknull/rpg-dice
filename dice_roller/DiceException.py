class DiceException(Exception):
    def __init__(self, message: str, errors):
        """Custom exception used throughout the dice roller.

        Parameters
        ----------
        message: str
            A short description of the error.
        errors: Any
            Additional error information.
        """
        super().__init__(message)
        self.errors = errors
