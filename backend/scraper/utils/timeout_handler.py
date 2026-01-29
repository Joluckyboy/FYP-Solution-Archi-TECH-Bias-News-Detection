"""
Timeout protection utilities using threading (works in gunicorn/Docker)
"""
import threading
import logging

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Custom exception for timeouts"""
    pass


def download_and_parse_article(article_obj, config, timeout_seconds=10):
    """
    Download and parse article with timeout protection using threading
    Works in multi-threaded environments (gunicorn, Docker)
    """
    result = [None]
    exception = [None]
    
    def target():
        try:
            article_obj.config = config
            article_obj.download()
            article_obj.parse()
            result[0] = article_obj
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        # Thread is still running - timeout occurred
        logger.warning(f"⏱️  Timeout ({timeout_seconds}s): {article_obj.url[:60]}")
        return None
    
    if exception[0]:
        logger.debug(f"Error downloading article: {str(exception[0])[:50]}")
        return None
    
    return result[0]
