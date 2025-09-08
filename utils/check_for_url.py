
import logging


async def check_for_url(browser, url):
    page = None
    try:
        for p in browser.pages:
            if p.url.startswith(url):
                page = p
                break
    except Exception:
        logging.exception("Failed to check for URL")
        
    return page