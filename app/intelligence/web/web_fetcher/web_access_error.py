class WebAccessError(Exception):
    """Raised when a URL cannot or may not be fetched — refused by the address guard,
    unreachable, too slow, too large, or answered with an error status. One exception
    type for all of them is the point: a tool catches nothing, the ToolExecutor turns
    it into an error result, and the model reads the sentence this carries and decides
    what to try next."""
