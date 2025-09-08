import pyperclip
from config import config

class MetamaskFunc:
    def __init__(self, page):
        self.metamask = page

    async def metamask_first_time_signin(self):
        await self.metamask.click("text=Get started")
        await self.metamask.click("#terms-of-use__checkbox")
        await self.metamask.click("data-testid=terms-of-use-scroll-button")
        await self.metamask.click("data-testid=terms-of-use-agree-button")
        await self.metamask.click("data-testid=onboarding-import-wallet")
        await self.metamask.click("data-testid=onboarding-import-with-srp-button")

        pyperclip.copy(config.METAMASK_PHRASE)
        await self.metamask.focus("data-testid=srp-input-import__srp-note")
        await self.metamask.keyboard.press("Control+V")
        await self.metamask.click("data-testid=import-srp-confirm")

        await self.metamask.fill("#create-password-new", config.METAMASK_PASSWORD)
        await self.metamask.fill("#create-password-confirm", config.METAMASK_PASSWORD)
        await self.metamask.click("data-testid=create-password-terms")
        await self.metamask.click("data-testid=create-password-submit")

        await self.metamask.click("data-testid=metametrics-no-thanks")
        await self.metamask.click("data-testid=onboarding-complete-done")
        await self.metamask.click("data-testid=pin-extension-done")
        await self.metamask.click("data-testid=not-now-button")

    async def metamask_login(self):
        await self.metamask.fill("data-testid=unlock-password", config.METAMASK_PASSWORD)
        await self.metamask.click("data-testid=unlock-submit")        

    