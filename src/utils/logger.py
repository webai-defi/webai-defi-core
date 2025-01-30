import logging


logger = logging.getLogger(__name__)

def log_exceptions(func):
    from functools import wraps
    if callable(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
                raise e

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
                raise e

        return async_wrapper if hasattr(func, "__call__") and callable(func) and func.__code__.co_flags & 0x80 else sync_wrapper

