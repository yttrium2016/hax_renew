import os
import random
import asyncio
from cf_clearance import async_cf_retry, stealth_async
from playwright.async_api import Playwright, async_playwright, Page
from simpleCaptchaSolver import reCapthaSolver, simpleSolver
import json


TRUECAPTCHA_USERID = os.environ.get("TRUECAPTCHA_USERID", "TRUECAPTCHA_USERID")
TRUECAPTCHA_APIKEY = os.environ.get(
    "TRUECAPTCHA_APIKEY", "TRUECAPTCHA_APIKEY")
SECRETID = os.environ.get("SECRETID", "SECRETID")
SECRETKEY = os.environ.get("SECRETKEY", "SECRETKEY")
USRNAME = os.environ.get("USRNAME", "USRNAME")
PASSWORD = os.environ.get("PASSWORD", "PASSWORD")
DRIVER = os.environ.get("DRIVER", "/usr/bin/chromedriver")
UA = os.environ.get(
    "UA", f"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(89,100)}.{random.randint(0,9)}.{random.randint(1000,9999)}.{random.randint(100,999)} Safari/537.36")

async def saveCookies(context):
# 保存状态
    storage = await context.storage_state()
    with open("state.json", "w") as f:
        f.write(json.dumps(storage))
 
async def loadCookies():
    # 加载状态
    try:
        with open("state.json","r") as f:
            storage_state = json.loads(f.read())
    except:
        storage_state = {}
    return storage_state

async def login(page: Page) -> None:
    await page.goto('https://hax.co.id/vps-info')  # 默认也为 30s 内加载界面
    res = await async_cf_retry(page)  # 过 cloudflare waf
    print("cf passed",res)

    await page.focus(".card")
    if page.url != 'https://hax.co.id/login':
        print("it seems that you has logined in",page.url)
        return

    # Fill [name="username"] [placeholder="Password"]
    await page.locator("[name=\"username\"]").fill(USRNAME)
    await page.locator("[placeholder=\"Password\"]").fill(PASSWORD)
    print("username & passed filled")

    # reCaptha Solve
    result = await reSolve(page)

    await page.wait_for_timeout(random.randint(1700, 5600))

    if result != 'false':
        # Click text=Submit
        await page.locator("text=Submit").focus()
        await page.keyboard.press("Enter")
        print("Submit clicked")

        try:
            result = await page.locator("//html/body/main/div/div/div[2]/div/div/div/div/div/div",timeout=60000).inner_text()
        except:
            result = page.url
    print(result)
    # await page.wait_for_timeout(65535)


async def renew(page: Page) -> None:
    # Go to https://hax.co.id/vps-renew
    await page.goto("https://hax.co.id/vps-renew")
    res = await async_cf_retry(page)  # 过 cf
    print("cf passed",res)

    # Click [input[name=\"web_address\"]]
    web_address = page.locator("input[name=\"web_address\"]")
    # Fill [input[name=\"web_address\"]]
    print("web_address placeholder: ",await web_address.get_attribute('placeholder'))
    await web_address.fill(await web_address.get_attribute('placeholder'))
    print("web_address filled")

    # Check input[name="agreement"]
    await page.locator("input[name=\"agreement\"]").focus()
    await page.keyboard.press(" ")
    # await page.locator("input[name=\"agreement\"]").check()
    print("agreement checked")

    await simpleSolve(page)
    # Click span[role="checkbox"]
    await reSolve(page)

    # Click button:has-text("Renew VPS")
    await page.wait_for_timeout(random.randint(1700, 5600))
    await page.locator("[name=\"submit_button\"]").focus()
    await page.keyboard.press("Enter")

    result = await page.locator("[id=\"response\"]").inner_text()
    while result == "Loading.....":
        try:
            result = await page.locator("[id=\"response\"]").inner_text()
        except:
            break
    print(result)


async def main() -> None:
    async with async_playwright() as playwright:
        # 初始化 browser 及其 上下文
        browser = await playwright.chromium.launch(headless=True,timeout=300000)
        context = await browser.new_context(
            user_agent=UA,
            viewport={"width":1920,"height":1080},
            storage_state=await loadCookies(),
        )

        # 初始化 特征隐藏 js
        js = """
        Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});
        """

        # Open new page
        page = await context.new_page()
        page.add_init_script(js)  # 注入 js
        page.set_default_timeout(300000)
        await stealth_async(page, pure=False)  # 进一步特征隐藏

        # await page.content() # 等待页面 不知道作用如何

        await login(page)
        await saveCookies(context)
        await renew(page)

        # ---------------------
        await context.close()
        await browser.close()


async def reSolve(page: Page, iframePath="") -> str:
    reSolver = reCapthaSolver(SECRETID, SECRETKEY, 0)
    auto_passed = await page.frame_locator("iframe[role=\"presentation\"]").locator("//*[@id=\"recaptcha-anchor\"]").get_attribute('aria-checked')
    print(auto_passed)
    if auto_passed == "true":
        return auto_passed

    # Click span[role="checkbox"]
    await page.wait_for_timeout(random.randint(1700, 3600))
    await page.frame_locator("iframe[role=\"presentation\"]").locator("span[role=\"checkbox\"]").focus()
    # await page.frame_locator("iframe[role=\"presentation\"]").locator("span[role=\"checkbox\"]").click()
    await page.keyboard.press("Enter")
    print("checkbox clicked")

    # Click #recaptcha-audio-button
    await page.wait_for_timeout(random.randint(2100, 2900))
    try:
        await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("#recaptcha-audio-button").focus()
        await page.keyboard.press("Enter")
    except:
        return await errhand(page,1)
    # await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("#recaptcha-audio-button").click()
    print("audio-button clicked")

    # Click a
    await page.wait_for_timeout(random.randint(1700, 5600))
    try:
        await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("[class=\"rc-audiochallenge-play-button\"]",timeout=30000).focus()
        await page.keyboard.press("Enter")
        print("play-button clicked")
    except:
        print("play-button click failed, auto pass to next step")
        # return await errhand(page,1)
    # await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("button:has-text(\"播放\")").click()
    audio_url = await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("a").get_attribute("href")
    print(audio_url)
    print("audio_url got success")

    if audio_url == 'https://developers.google.com/recaptcha/docs/faq#my-computer-or-network-may-be-sending-automated-queries':
        return await errhand(page,1)
    result = reSolver._solve_p(audio_url)

    if not result:
        return "false"

    await page.wait_for_timeout(random.randint(3700, 5600))
    await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("#audio-response").focus()
    await page.keyboard.press("Enter")
    # await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("#audio-response").click()
    await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("#audio-response").fill(result)
    print("audio-response filled")

    # Click recaptcha-verify-button
    await page.wait_for_timeout(random.randint(3700, 5600))
    await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("[id=\"recaptcha-verify-button\"]").focus()
    await page.keyboard.press("Enter")
    # await page.frame_locator("//html/body/div[10]/div[4]/iframe").locator("text=验证").click()
    print("verify-button clicked")
    return result

async def errhand(page,head=0):
    if head :print("please hand login")
    while (head and (await page.frame_locator("iframe[role=\"presentation\"]").locator("//*[@id=\"recaptcha-anchor\"]").get_attribute("aria-checked") == 'false')):
            continue
    return await page.frame_locator("iframe[role=\"presentation\"]").locator("//*[@id=\"recaptcha-anchor\"]").get_attribute("aria-checked")

async def simpleSolve(page: Page, iframePath="") -> str:
    simple_Solver = simpleSolver(TRUECAPTCHA_USERID, TRUECAPTCHA_APIKEY)
    await page.locator("img[id=\"captcha\"]").screenshot(path="captcha.png")
    result: dict = simple_Solver.solve("captcha.png")
    # Fill input[name="captcha"]
    print(f"the num_code is {result}")
    await page.locator("input[name=\"captcha\"]").fill(result.get('result'))
    print(f"the captcha code filled")
    return result.get('result')

asyncio.run(main())
