import logging
import os
from functools import wraps
from src.config import settings

# Создание папки для логов, если она не существует
log_directory = settings.LOGS_URL
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Пути к файлам логов
log_file_info = os.path.join(log_directory, "info.log")
log_file_error = os.path.join(log_directory, "error.log")
log_file_all = os.path.join(log_directory, "app.log")

# Создание логгера
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)  # Общий уровень логирования

# Форматтер для логов
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

# === Обработчик для всех логов ===
file_handler_all = logging.FileHandler(log_file_all)
file_handler_all.setLevel(logging.DEBUG)
file_handler_all.setFormatter(formatter)

# === Обработчик для INFO логов ===
file_handler_info = logging.FileHandler(log_file_info)
file_handler_info.setLevel(logging.INFO)
file_handler_info.setFormatter(formatter)

# === Обработчик для WARNING и ERROR ===
file_handler_error = logging.FileHandler(log_file_error)
file_handler_error.setLevel(logging.WARNING)
file_handler_error.setFormatter(formatter)

# === Обработчик для консоли (только WARNING и выше) ===
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

# Добавляем обработчики в логгер
logger.addHandler(file_handler_all)
logger.addHandler(file_handler_info)
logger.addHandler(file_handler_error)
logger.addHandler(console_handler)

# === Декоратор для логирования исключений ===
def log_exceptions(func):
    if callable(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__} | Args: {args}, Kwargs: {kwargs} | Error: {str(e)}", exc_info=True)
                raise e

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__} | Args: {args}, Kwargs: {kwargs} | Error: {str(e)}", exc_info=True)
                raise e

        return async_wrapper if hasattr(func, "__call__") and callable(func) and func.__code__.co_flags & 0x80 else sync_wrapper
