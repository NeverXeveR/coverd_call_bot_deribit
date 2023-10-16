import logging

# Create a file handler to log messages to a file
log_filename = 'bot.log'
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'))

# Create a console handler to log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'))

# Add the handlers to the root logger
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(console_handler)
