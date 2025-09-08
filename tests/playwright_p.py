from playwright.sync_api import sync_playwright
import pyperclip
import time

EXTENSION_PATH = r"C:\Users\deboj\VSCODE\project_liquidity_rebalance\nkbihfbeogaeaoehlefnkodbefgpgknn"
USER_DATA_DIR = r"C:\Users\deboj\VSCODE\project_liquidity_rebalance\playwright_profile"
METAMASK_PHRASE = "dynamic bacon gas sauce daring scan drama entire cruel local model reform"
METAMASK_PASSWORD = "debojit80"

def launch_browser(p):
    browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
        args=[
            f"--disable-extensions-except={EXTENSION_PATH}",
            f"--load-extension={EXTENSION_PATH}",
            "--start-maximized",
        ],
        viewport=None,
    )

    # Open a blank page just to get a page object
    page = browser.new_page()
    page.goto("https://www.google.com")
    browser.pages[0].close()

    #close default page

    time.sleep(8)
    metamask = browser.pages[1]
    metamask.click("text=Get started")
    metamask.click("#terms-of-use__checkbox")
    metamask.click("data-testid=terms-of-use-scroll-button")
    metamask.click("data-testid=terms-of-use-agree-button")
    metamask.click("data-testid=onboarding-import-wallet")
    metamask.click("data-testid=onboarding-import-with-srp-button")

    pyperclip.copy(METAMASK_PHRASE)
    metamask.focus("data-testid=srp-input-import__srp-note")
    metamask.keyboard.press("Control+V")
    metamask.click("data-testid=import-srp-confirm")

    metamask.fill("#create-password-new", METAMASK_PASSWORD)
    metamask.fill("#create-password-confirm", METAMASK_PASSWORD)
    metamask.click("data-testid=create-password-terms")
    metamask.click("data-testid=create-password-submit")

    metamask.click("data-testid=metametrics-no-thanks")
    metamask.click("data-testid=onboarding-complete-done")
    metamask.click("data-testid=pin-extension-done")
    metamask.click("data-testid=not-now-button")


    # if(metamask.is_visible("data-testid=create-password")):
    #     if(metamask.is_checked("data-testid=create-password-terms")):
    #     #metamask.wait_for_selector("#create-password-new")
    #         value = metamask.eval_on_selector("#create-password-new", "el => el.value")
    #         print("Input value:", value)



    # Open MetaMask popup (replace with actual popup HTML if different)
    input("Press Enter to close...")
    browser.close()


with sync_playwright() as p:
    launch_browser(p)