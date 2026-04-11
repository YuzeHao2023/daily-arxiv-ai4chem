class ArxivDailyError(Exception):
    """Base exception for daily-arxiv errors."""

class ArxivFetchError(ArxivDailyError):
    """arXiv API fetch failed."""

class GitHubAPIError(ArxivDailyError):
    """GitHub API call failed."""

class FileOperationError(ArxivDailyError):
    """File read/write failed."""

class ConfigError(ArxivDailyError):
    """Configuration load failed."""
