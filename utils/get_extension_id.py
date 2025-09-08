import logging


async def get_extension_id(browser):
    extension_id = None
    try:
        if getattr(browser, "service_workers", None):
            for sw in browser.service_workers:
                url = getattr(sw, "url", "")
                if url.startswith("chrome-extension://"):
                    extension_id = url.split("/")[2]
                    break
        if not extension_id:
            for p in browser.pages:
                url = p.url
                if url.startswith("chrome-extension://"):
                    extension_id = url.split("/")[2]
                    break
                
    except Exception:
        logging.exception("Failed to get MetaMask extension id")
    return extension_id