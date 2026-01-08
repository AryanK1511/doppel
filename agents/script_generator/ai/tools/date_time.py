from datetime import datetime

from common.logger import logger


def get_current_date_info() -> str:
    """
    Get the current date and time information. Use this tool to understand what 'latest' or 'current' means in terms of dates when searching for trends or news.
    """
    logger.info("Getting current date and time information")
    now = datetime.now()
    return f"Current date: {now.strftime('%B %d, %Y')}. Current year: {now.year}. Current month: {now.strftime('%B')} ({now.month}). Current day: {now.day}. This is the temporal context for understanding what 'latest' or 'current' means."
