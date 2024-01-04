import sys
import os

import asyncio
from pyppeteer import launch


def capture(url, dst, width=1000):
    async def _cap_async():
        browser = await launch(args=["--no-sandbox"])
        page = await browser.newPage()
        await page.goto(url, {"waitUntil": "networkidle0"})
        await page.evaluateHandle("document.fonts.ready")
        await page.setViewport({"width": width, "height": width * 2})
        await page.screenshot({"path": dst, "fullPage": True})
        await browser.close()

    asyncio.get_event_loop().run_until_complete(_cap_async())


if __name__ == "__main__":
    capture(f"file://{os.path.abspath(sys.argv[1])}", sys.argv[2])
