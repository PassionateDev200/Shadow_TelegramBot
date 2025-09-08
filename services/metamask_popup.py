
class MetamaskPopup:
    def __init__(self, popup_page):
        self.metamask_popup = popup_page

    async def popup_viewport(self):
        await self.metamask_popup.evaluate("window.resizeTo(400, 600)")
        await self.metamask_popup.wait_for_load_state("networkidle")
