import time
import threading
from collections import defaultdict

# Thread lock to guarantee safety across concurrent Gradio worker threads
_limiter_lock = threading.Lock()

# Thread-safe dictionary storing historical request timestamps per user
# Structure: { "user_license_key": [timestamp1, timestamp2, ...] }
_upload_history = defaultdict(list)

class RateLimitExceededError(Exception):
    """Custom exception raised when a user bypasses their maximum permitted action rate."""
    def __init__(self, message="Too many uploads! Please wait a moment before trying again.", retry_after=0):
        super().__init__(message)
        self.retry_after = retry_after


def check_upload_limit(user_key: str, max_uploads: int = 5, window_seconds: int = 60) -> bool:
    """
    Enforces a strict rolling/sliding window rate limit on a specific user identifier.
    
    Args:
        user_key (str): The unique identifier for the user (e.g., license key or IP).
        max_uploads (int): Maximum uploads allowed within the sliding window duration.
        window_seconds (int): The length of the rolling window in seconds.
        
    Raises:
        RateLimitExceededError: If the user has crossed their permitted limit threshold.
        
    Returns:
        bool: True if the request is safely within limits and successfully registered.
    """
    now = time.time()
    cutoff_time = now - window_seconds

    with _limiter_lock:
        # 1. Prune timestamps older than our current rolling window window
        user_logs = _upload_history[user_key]
        _upload_history[user_key] = [ts for ts in user_logs if ts > cutoff_time]
        
        # 2. Check if the active remaining logs breach our security threshold
        current_count = len(_upload_history[user_key])
        if current_count >= max_uploads:
            # Calculate exactly how long they need to wait before their oldest log expires
            oldest_log = _upload_history[user_key][0]
            seconds_to_wait = max(1, int((oldest_log + window_seconds) - now))
            
            raise RateLimitExceededError(
                message=f"Upload limit exceeded. You can upload again in {seconds_to_wait} seconds.",
                retry_after=seconds_to_wait
            )
            
        # 3. If within limits, log the current timestamp and grant access
        _upload_history[user_key].append(now)
        return True


def clear_user_history(user_key: str):
    """Utility function to clear a user's rate history (useful for testing or cache flushes)."""
    with _limiter_lock:
        if user_key in _upload_history:
            del _upload_history[user_key]
            
