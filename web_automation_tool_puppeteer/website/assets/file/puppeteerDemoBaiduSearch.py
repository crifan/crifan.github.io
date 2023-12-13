# Function: pyppeteer (python version puppeteer) do baidu search
# Author: Crifan Li
# Update: 20210330

import asyncio
from pyppeteer import launch

async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()

    await page.setJavaScriptEnabled(enabled=True)

    baiduUrl = "https://www.baidu.com"
    await page.goto(baiduUrl)
    # await page.screenshot({'path': 'baidu.png'})

    ################################################################################
    # Input text
    ################################################################################
    searchStr = "crifan"

    # SearchInputSelector = "input[id=kw]"
    SearchInputSelector = "input[id='kw']"

    # SearchInputXpath = "//input[@id='kw']"
    # searchInputElem = page.xpath(SearchInputXpath)

    # # Input method 1: selector + click + keyboard type
    # searchInputElem = await page.querySelector(SearchInputSelector)
    # print("searchInputElem=%s" % searchInputElem)
    # await searchInputElem.click()
    # await page.keyboard.type(searchStr)

    # Input method 2: focus then type
    # await page.focus(SearchInputSelector)
    # await page.keyboard.type(searchStr)

    # Input method 3: selector and input once using type
    await page.type(SearchInputSelector, searchStr, delay=20)

    ################################################################################
    # Trigger search
    ################################################################################

    # Method 1: press ENTER key
    await page.keyboard.press('Enter')

    # # Method 2: locator search button then click
    # SearchButtonSelector = "input[id='su']"
    # searchButtonElem = await page.querySelector(SearchButtonSelector)
    # print("searchButtonElem=%s" % searchButtonElem)
    # await searchButtonElem.click()
    # # await searchButtonElem.press("Enter")

    ################################################################################
    # Wait page reload complete
    ################################################################################
    SearchFoundWordsSelector = 'span.nums_text'
    SearchFoundWordsXpath = "//span[@class='nums_text']"

    # await page.waitForSelector(SearchFoundWordsSelector)
    # await page.waitFor(SearchFoundWordsSelector)
    # await page.waitForXPath(SearchFoundWordsXpath)
    # Note: all above exception: 发生异常: ElementHandleError Evaluation failed: TypeError: MutationObserver is not a constructor
    #   so change to following

    # # Method 1: just wait
    # await page.waitFor(2000) # millisecond

    # Method 2: wait element showing
    SingleWaitSeconds = 1
    while not await page.querySelector(SearchFoundWordsSelector):
      print("Still not found %s, wait %s seconds" % (SearchFoundWordsSelector, SingleWaitSeconds))
      await asyncio.sleep(SingleWaitSeconds)
      # pass

    ################################################################################
    # Extract result
    ################################################################################

    resultASelector = "h3[class^='t'] a"
    searchResultAList = await page.querySelectorAll(resultASelector)
    # print("searchResultAList=%s" % searchResultAList)
    searchResultANum = len(searchResultAList)
    print("Found %s search result:" % searchResultANum)
    for curIdx, aElem in enumerate(searchResultAList):
      curNum = curIdx + 1
      print("%s [%d] %s" % ("-"*20, curNum, "-"*20))
      aTextJSHandle = await aElem.getProperty('textContent')
      # print("type(aTextJSHandle)=%s" % type(aTextJSHandle))
      # type(aTextJSHandle)=<class 'pyppeteer.execution_context.JSHandle'>
      # print("aTextJSHandle=%s" % aTextJSHandle)
      # aTextJSHandle=<pyppeteer.execution_context.JSHandle object at 0x10309c9b0>
      title = await aTextJSHandle.jsonValue()
      # print("type(title)=%s" % type(title))
      # type(title)=<class 'str'>
      print("title=%s" % title)

      baiduLinkUrl = await (await aElem.getProperty("href")).jsonValue()
      print("baiduLinkUrl=%s" % baiduLinkUrl)

    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
