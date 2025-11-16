class PFSException(Exception):
    def __init__(self, message: str, error_code: int = None):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        if self.error_code is not None:
            return f"[Code {self.error_code}] {super().__str__()}"
        return super().__str__()

class NoMetadataException(PFSException):
    pass