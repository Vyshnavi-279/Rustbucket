class ScanError(Exception):
    """Raised when a scan cannot be completed for any reason.

    Person 1's worker expects this exception to carry a short, human
    readable message that can be shown to the end user.
    """