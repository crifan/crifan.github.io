#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2020-09-02 21:22:43
# Project: autohome_20200902

import string
import re
import copy
import json

from lxml import etree

# from bs4 import BeautifulSoup

from pyspider.libs.base_handler import *

AutohomeHost = "https://www.autohome.com.cn"
CarSpecPrefix = "%s/spec" % AutohomeHost # "https://www.autohome.com.cn/spec/%s/"

class Handler(BaseHandler):
    UserAgent_Mac_Chrome = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    crawl_config = {
        "headers": {
            "User-Agent": UserAgent_Mac_Chrome,
        }
    }

    def genSpecUrl(self, specId):
        # return "%s/%s" % (CarSpecPrefix, specId)
        return "%s/%s/" % (CarSpecPrefix, specId)

    def genConfigSpecUrl(self, specId):
        configSpecTemplate = "https://car.autohome.com.cn/config/spec/%s.html"
        # https://car.autohome.com.cn/config/spec/43593.html
        return configSpecTemplate % specId
    
    def to10KPrice(self, originPrice):
        tenKPrice = ""
        # 19.08 / '19.08' -> '19.08万'
        if isinstance(originPrice, str):
            tenKPrice = "%s万" % originPrice
        elif isinstance(originPrice, float):
            tenKPrice = "%.2f万" % originPrice
        elif isinstance(originPrice, int):
            tenKPrice = "%s.00万" % originPrice
        
        return tenKPrice


    def extractSpecId(self, specUrl):
        carSpedId = ""
        # https://www.autohome.com.cn/spec/41511/#pvareaid=3454492
        # https://www.autohome.com.cn/spec/2304/
        foundSpecId = re.search("spec/(?P<specId>\d+)", specUrl)
        print("foundSpecId=%s" % foundSpecId)
        if foundSpecId:
            carSpedId = foundSpecId.group("specId")
            print("carSpedId=%s" % carSpedId)
        return carSpedId

    # @every(minutes=24 * 60)
    def on_start(self):
        # autohomeEntryUrl = "https://www.autohome.com.cn/car/"
        # self.crawl(autohomeEntryUrl, callback=self.carBrandListCallback)
        for eachLetter in list(string.ascii_lowercase):
            letterUpper = eachLetter.upper()
            # # for debug
            # letterUpper = "H"
            print("letterUpper=%s" % letterUpper)
            self.crawl("https://www.autohome.com.cn/grade/carhtml/%s.html" % eachLetter,
                save={"initials": letterUpper},
                callback=self.gradCarHtmlPage)

    @catch_status_code_error
    def gradCarHtmlPage(self, response):
        print("gradCarHtmlPage: response=", response)

        # picSeriesItemList = response.doc('.rank-list-ul li div a[href*="/pic/series"]').items()
        # print("picSeriesItemList=", picSeriesItemList)
        # print("len(picSeriesItemList)=%s"%(len(picSeriesItemList)))
        # for each in picSeriesItemList:
        #     self.crawl(each.attr.href, callback=self.picSeriesPage)

        saveDict = response.save
        print("saveDict=", saveDict)
        initials = saveDict["initials"]
        print("initials=", initials)
        respText = response.text
        # print("respText=", respText)

        """
        <dl id="33" olr="6">
            <dt><a href="//car.autohome.com.cn/price/brand-33.html#pvareaid=2042362"><img width="50" height="50"
                    src="//car2.autoimg.cn/cardfs/series/g26/M0B/AE/B3/100x100_f40_autohomecar__wKgHEVs9u5WAV441AAAKdxZGE4U148.png"></a>
                <div><a href="//car.autohome.com.cn/price/brand-33.html#pvareaid=2042362">奥迪</a></div>
            </dt>
        """
        # brandDoc = response.doc('dl dt')
        # print("brandDoc=%s" % brandDoc)
        # brandListDoc = response.doc('dl[id and orl] dt')
        # dlListDoc = response.doc('dl[id and orl]').items()
        # dlListDoc = response.doc("dl[id*=''][orl*='']").items()
        # dlListDoc = response.doc("dl[orl*='']").items()
        # dlListDoc = response.doc("dl").items()
        # dlListDoc = response.doc("dl:regex(id, \d+)").items()
        # dlListDoc = response.doc("dl:regex(id,[0-9])").items()
        # dlListDoc = response.doc("dl[id]").items()
        dlListDoc = response.doc("dl[olr]").items()
        print("type(dlListDoc)=%s" % type(dlListDoc))
        dlList = list(dlListDoc)
        print("len(dlList)=%s" % len(dlList))
        print("dlList=%s" % dlList)
        for curBrandIdx, eachDlDoc in enumerate(dlList):
            print("%s [%d] %s" % ('#'*30, curBrandIdx, '#'*30))

            dtDoc = eachDlDoc.find("dt")
            # print("dtDoc=%s" % dtDoc)
            # <a href="//car.autohome.com.cn/price/brand-33.html#pvareaid=2042362"><img width="50" height="50" src="//car2.autoimg.cn/cardfs/series/g26/M0B/AE/B3/100x100_f40_autohomecar__wKgHEVs9u5WAV441AAAKdxZGE4U148.png"></a>
            brandLogoDoc = dtDoc.find('a img')
            # print("brandLogoDoc=%s" % brandLogoDoc)
            carBrandLogoUrl = brandLogoDoc.attr["src"]
            print("carBrandLogoUrl=%s" % carBrandLogoUrl)
            # <div><a href="//car.autohome.com.cn/price/brand-33.html#pvareaid=2042362">奥迪</a></div>
            brandADoc = dtDoc.find('div a')
            print("brandADoc=%s" % brandADoc)
            # <a href="https://car.autohome.com.cn/price/brand-63.html#pvareaid=2042362">日产</a>
            carBrandName = brandADoc.text()
            print("carBrandName=%s" % carBrandName)
            carBrandUrl = brandADoc.attr["href"]
            print("carBrandUrl=%s" % carBrandUrl)
            carBrandId = ""
            foundBrandId = re.search("brand-(?P<carBrandId>\d+)\.html", carBrandUrl)
            # print("foundBrandId=%s" % foundBrandId)
            if foundBrandId:
                carBrandId = foundBrandId.group("carBrandId")
            print("carBrandId=%s" % carBrandId) # 63

            # <div class="h3-tit"><a href="//car.autohome.com.cn/price/brand-33-9.html#pvareaid=2042363">一汽-大众奥迪</a></div>
            # merchantDocGenerator = response.doc("dd div[class='h3-tit'] a").items()
            # ddDoc = eachDlDoc.find("dd")
            ddDoc = eachDlDoc.find("dd")
            # print("ddDoc=%s" % ddDoc)

            merchantDocGenerator = ddDoc.items("div[class='h3-tit'] a")
            merchantDocList = list(merchantDocGenerator)
            # print("merchantDocList=%s" % merchantDocList)
            merchantDocLen = len(merchantDocList)
            print("merchantDocLen=%s" % merchantDocLen)

            # <ul class="rank-list-ul" 0>
            # merchantRankDocGenerator = response.doc("dd ul[class='rank-list-ul']")
            # merchantRankDocGenerator = response.doc("dd ul[class='rank-list-ul']").items()
            merchantRankDocGenerator = ddDoc.items("ul[class='rank-list-ul']")
            merchantRankDocList = list(merchantRankDocGenerator)
            # print("merchantRankDocList=%s" % merchantRankDocList)
            merchantRankDocListLen = len(merchantRankDocList)
            print("merchantRankDocListLen=%s" % merchantRankDocListLen)

            for curIdx, merchantItem  in enumerate(merchantDocList):
            # for curIdx, merchantItem  in enumerate(merchantDocGenerator):
                # print("%s" % "="*80)
                print("%s [%d] %s" % ('='*30, curIdx, '='*30))
                # print("type(merchantItem)=%s" % type(merchantItem))
                # print("[%d] merchantItem=%s" % (curIdx, merchantItem))
                # print("[%d] merchantItem=%s" % (curIdx, merchantItem))
                carMerchantName = merchantItem.text()
                print("carMerchantName=%s" % carMerchantName)
                merchantItemAttr = merchantItem.attr
                # print("merchantItemAttr=%s" % merchantItemAttr)
                carMerchantUrl = merchantItemAttr["href"]
                print("carMerchantUrl=%s" % carMerchantUrl)

                # curSubBrandDict = {
                #     "brandName": brandName,
                #     "carBrandLogoUrl": carBrandLogoUrl,
                #     "carMerchantName": carMerchantName,
                #     "carMerchantUrl": carMerchantUrl,
                # }
                # self.send_message(self.project_name, curSubBrandDict, url=carMerchantUrl)

                merchantRankDoc = merchantRankDocList[curIdx]
                # print("merchantRankDoc=%s" % merchantRankDoc)
                # print("type(merchantRankDoc)=%s" % type(merchantRankDoc))

                # type(merchantRankDoc)=<class 'lxml.html.HtmlElement'>
                # merchantRankHtml = etree.tostring(merchantRankDoc)

                # type(merchantRankDoc)=<class 'pyquery.pyquery.PyQuery'>
                # merchantRankHtml = merchantRankDoc.html()

                # print("merchantRankHtml=%s" % merchantRankHtml)

                # <li id="s3170">
                # carSeriesDocGenerator = merchantRankDoc.find("li")
                # carSeriesDocGenerator = merchantRankDoc.find("li[id*='s']")
                carSeriesDocGenerator = merchantRankDoc.items("li[id*='s']")
                # print("type(carSeriesDocGenerator)=%s" % type(carSeriesDocGenerator))
                carSeriesDocList = list(carSeriesDocGenerator)
                # print("type(carSeriesDocList)=%s" % type(carSeriesDocList))
                # print("carSeriesDocList=%s" % carSeriesDocList)
                carSeriesDocListLen = len(carSeriesDocList)
                # print("carSeriesDocListLen=%s" % carSeriesDocListLen)
                
                for curSeriesIdx, eachCarSeriesDoc in enumerate(carSeriesDocList):
                    print("%s [%d] %s" % ('-'*30, curSeriesIdx, '-'*30))
                    # print("[%d] eachCarSeriesDoc=%s" % (curSeriesIdx, eachCarSeriesDoc))
                    # print("type(eachCarSeriesDoc)=%s" % type(eachCarSeriesDoc)) # type(eachCarSeriesDoc)=<class 'lxml.html.HtmlElement'>
                    # <h4><a href="//www.autohome.com.cn/3170/#levelsource=000000000_0&pvareaid=101594">奥迪A3</a></h4>
                    carSeriesInfoDoc = eachCarSeriesDoc.find("h4 a")
                    # print("type(carSeriesInfoDoc)=%s" % type(carSeriesInfoDoc))
                    # print("carSeriesInfoDoc=%s" % carSeriesInfoDoc)
                    carSeriesName = carSeriesInfoDoc.text()
                    print("carSeriesName=%s" % carSeriesName)
                    carSeriesUrl = carSeriesInfoDoc.attr.href
                    print("carSeriesUrl=%s" % carSeriesUrl)

                    # <div>指导价：<a class="red" href="//www.autohome.com.cn/3170/price.html#pvareaid=101446">19.32-23.46万</a></div>
                    # 厂商指导价=厂商建议零售价格=MSRP=Manufacturer's Suggested Retail Price
                    # carSeriesMsrpDoc = eachCarSeriesDoc.find("div a")
                    carSeriesMsrpDoc = eachCarSeriesDoc.find("div a[class='red']")
                    # print("carSeriesMsrpDoc=%s" % carSeriesMsrpDoc)
                    carSeriesMsrp = carSeriesMsrpDoc.text()
                    print("carSeriesMsrp=%s" % carSeriesMsrp)
                    carSeriesMsrpUrl = carSeriesMsrpDoc.attr.href
                    print("carSeriesMsrpUrl=%s" % carSeriesMsrpUrl)

                    carSeriesDict = {
                        "carBrandName": carBrandName,
                        "carBrandId": carBrandId,
                        "carBrandLogoUrl": carBrandLogoUrl,
                        "carMerchantName": carMerchantName,
                        "carMerchantUrl": carMerchantUrl,
                        "carSeriesName": carSeriesName,
                        "carSeriesUrl": carSeriesUrl,
                        "carSeriesMsrp": carSeriesMsrp,
                        "carSeriesMsrpUrl": carSeriesMsrpUrl,
                    }
                    # self.send_message(self.project_name, carSeriesDict, url=carSeriesUrl)
                    self.crawl(carSeriesUrl,
                        callback=self.carSeriesDetailPage,
                        save=carSeriesDict,
                    )

    @catch_status_code_error
    def carSeriesDetailPage(self, response):
        print("in carSeriesDetailPage")
        carSeriesDict = response.save
        print("carSeriesDict=%s" % carSeriesDict)

        carModelDict = copy.deepcopy(carSeriesDict)

        carSeriesUrl = response.url
        print("carSeriesUrl=%s" % carSeriesUrl)

        carSeriesMainImgUrl = ""
        # carSeriesId = ""
        carSeriesLevelId = ""
        carSeriesMsrp = ""
        carSeriesMinPrice = ""
        carSeriesMaxPrice = ""

        # carSeriesUrl=https://www.autohome.com.cn/2123/#levelsource=000000000_0&pvareaid=101594
        foundSeriesId = re.search("www\.autohome\.com\.cn/(?P<seriesId>\d+)/", carSeriesUrl)
        carSeriesId = foundSeriesId.group("seriesId")
        # carSeriesId = int(carSeriesId)
        print("carSeriesId=%s" % carSeriesId) # 2123
        carModelDict["carSeriesId"] = carSeriesId

        carSeriesHtml = response.text
        print("type(carSeriesHtml)=%s" % type(carSeriesHtml)) # <class 'str'>
        # print("carSeriesHtml=%s" % carSeriesHtml)

        foundLevelId = re.search("var\s+levelid\s+=", carSeriesHtml)
        print("foundLevelId=%s" % foundLevelId)
        isNewLayoutHtml = bool(foundLevelId)
        print("isNewLayoutHtml=%s" % isNewLayoutHtml)
        foundShowCityId = re.search("var\s+showCityId\s+=", carSeriesHtml)
        print("foundShowCityId=%s" % foundShowCityId)
        isOldLayoutHtml = bool(foundShowCityId)
        print("isOldLayoutHtml=%s" % isOldLayoutHtml)

        if isOldLayoutHtml:
            # Q开头
            # https://www.autohome.com.cn/grade/carhtml/q.html
            # ->
            # 东风悦达起亚-千里马
            # https://www.autohome.com.cn/142/#levelsource=000000000_0&pvareaid=101594
            # 其他：
            # 
            # 一汽丰田-花冠
            # https://www.autohome.com.cn/109/#levelsource=000000000_0&pvareaid=101594
            # 
            # 昶洧-昶洧 SUV
            # https://www.autohome.com.cn/4550/#levelsource=000000000_0&pvareaid=101594

            """
            <div class="car_detail " id="tab1-2">
                <div class="models">
                <!--年代-->
                    <div class="header">
                        <div class="car_price">
                            <span class="years">2005款</span>
                            <span class="price">指导价（停售）：<strong class="red">6.28万-9.18万</strong></span>
                            <span class="price">二手车价格：<strong class="red"><a class='cd60000' href='//www.che168.com/china/qiya/qianlima/a0_0msdgscncgpiltocsp1exs276/?pvareaid=103693'>0.39万-1.30万</a></strong></span>
            。。。
            <div class="car_detail current" id="tab1-1">
                <div class="models">
                    <!--年代-->
                    <div class="header">
                        <div class="car_price">
                            <span class="years">2006款</span>
                            <span class="price">指导价（停售）：<strong class="red">7.28万-8.58万</strong></span>
            。。。
            """
            carDetailDivGenerator = response.doc("div[class^='car_detail']").items()
            print("carDetailDivGenerator=%s" % carDetailDivGenerator)
            carDetailDivList = list(carDetailDivGenerator)
            print("carDetailDivList=%s" % carDetailDivList)
            for curDivIdx, eachCarDetailDoc in enumerate(carDetailDivList):
                print("%s [%d] %s" % ('#'*30, curDivIdx, '#'*30))

                if curDivIdx == 0:
                    # use first car model as series: main img, msrp, ...
                    """
                    <div class="models_info">
                        <dl class='models_pics'>
                            <dt><a href='//car.autohome.com.cn/photolist/series/2305/23796.html?pvareaid=101468'><img
                                src='https://car0.autoimg.cn/upload/spec/1344/t_1344388912334.jpg' width='240'
                                height='180' /></a></dt>
                    """
                    # modelMainImgDocListGenerator = response.doc("div[class='models_info'] dl[class='models_pics'] dt a img").items()
                    # modelMainImgDocList = list(modelMainImgDocListGenerator)
                    # firstModelMainImgDoc = modelMainImgDocList[0]
                    firstModelMainImgDoc = eachCarDetailDoc.find("div[class='models_info'] dl[class='models_pics'] dt a img")
                    firstModelMainImgUrl = firstModelMainImgDoc.attr["src"]
                    print("firstModelMainImgUrl=%s" % firstModelMainImgUrl)
                    carSeriesMainImgUrl = firstModelMainImgUrl
                    print("carSeriesMainImgUrl=%s" % carSeriesMainImgUrl)

                    carModelDict["carSeriesMainImgUrl"] = carSeriesMainImgUrl

                    # <div class="car_price">
                    #   <span class="price">指导价（停售）：<strong class="red">7.28万-8.58万</strong></span>
                    carPriceStrongDocGenerator = eachCarDetailDoc.items("div[class='car_price'] span[class='price'] strong[class='red']")
                    print("carPriceStrongDocGenerator=%s" % carPriceStrongDocGenerator)
                    if carPriceStrongDocGenerator:
                        carPriceStrongDocList = list(carPriceStrongDocGenerator)
                        print("carPriceStrongDocList=%s" % carPriceStrongDocList)
                        carPriceStrongDoc = carPriceStrongDocList[0]
                        print("carPriceStrongDoc=%s" % carPriceStrongDoc)
                        carPriceMinMax = carPriceStrongDoc.text()
                        print("carPriceMinMax=%s" % carPriceMinMax)
                        if carPriceMinMax:
                            foundMinMax = re.search("(?P<minPrice>[\d\.]+)万-(?P<maxPrice>[\d\.]+)万", carPriceMinMax)
                            print("foundMinMax=%s" % foundMinMax)
                            if foundMinMax:
                                minPrice = foundMinMax.group("minPrice")
                                print("minPrice=%s" % minPrice)
                                minPriceFloat = float(minPrice)
                                print("minPriceFloat=%s" % minPriceFloat)
                                maxPrice = foundMinMax.group("maxPrice")
                                print("maxPrice=%s" % maxPrice)
                                maxPriceFloat = float(maxPrice)
                                print("maxPriceFloat=%s" % maxPriceFloat)
                                averageMsrcPrice = (minPriceFloat + maxPriceFloat) / 2.0
                                print("averageMsrcPrice=%s" % averageMsrcPrice)

                                # carSeriesMsrp = "%.2f万" % averageMsrcPrice
                                carSeriesMsrp = self.to10KPrice(averageMsrcPrice)
                                print("carSeriesMsrp=%s" % carSeriesMsrp)
                                # carSeriesMinPrice = "%.2f万" % minPriceFloat
                                carSeriesMinPrice = self.to10KPrice(minPriceFloat)
                                print("carSeriesMinPrice=%s" % carSeriesMinPrice)
                                # carSeriesMaxPrice = "%.2f万" % maxPriceFloat
                                carSeriesMaxPrice = self.to10KPrice(maxPriceFloat)
                                print("carSeriesMaxPrice=%s" % carSeriesMaxPrice)

                                carModelDict["carSeriesMsrp"] = carSeriesMsrp
                                carModelDict["carSeriesMinPrice"] = carSeriesMinPrice
                                carModelDict["carSeriesMaxPrice"] = carSeriesMaxPrice
                    print("")

                self.processSingleCarDetailDiv(carModelDict, eachCarDetailDoc)

        elif isNewLayoutHtml:
            # https://www.autohome.com.cn/3170/#levelsource=000000000_0&pvareaid=101594

            """
            <div class="information-pic">
                <div class="pic-main">
                。。。
                        <picture>
                            。。。
                            <img sizes="380px" width="380" height="285"
                                src="//car2.autoimg.cn/cardfs/product/g1/M04/0B/F0/380x285_0_q87_autohomecar__ChwFqV8YG-aACch8AAkAdoJoSYM874.jpg"
                                srcset="//car2.autoimg.cn/cardfs/product/g1/M04/0B/F0/380x285_0_q87_autohomecar__ChwFqV8YG-aACch8AAkAdoJoSYM874.jpg 380w, //car2.autoimg.cn/cardfs/product/g1/M04/0B/F0/760x570_0_q87_autohomecar__ChwFqV8YG-aACch8AAkAdoJoSYM874.jpg 760w">
                        </picture>
            """
            mainImgDoc = response.doc("div[class='information-pic'] div[class='pic-main'] picture img")
            print("mainImgDoc=%s" % mainImgDoc)
            carSeriesMainImgUrl = mainImgDoc.attr["src"]
            print("carSeriesMainImgUrl=%s" % carSeriesMainImgUrl)
            carModelDict["carSeriesMainImgUrl"] = carSeriesMainImgUrl

            """
            <script type="text/javascript">
                。。。
                var seriesid = '2123';
                var seriesname='哈弗H6';
                var yearid = '0';
                var brandid = '181';
                var levelid = '17';
                var levelname='紧凑型SUV';
                var fctid = '4';
                var SeriesMinPrice='9.80';
                var SeriesMaxPrice='14.10';
            """

            infoKeyList = [
                "seriesid",
                # "seriesname", # has got
                # "yearid", # no need
                "brandid",
                "levelid",
                "levelname",
                # "fctid", # unknown meaning
                "SeriesMinPrice",
                "SeriesMaxPrice",
            ]
            InfoDict = {}
            for eachInfoKey in infoKeyList:
                curPattern = "var\s+%s\s*=\s*'(?P<infoValue>[^']+)'\s*;" % eachInfoKey
                print("curPattern=%s" % curPattern)
                foundInfo = re.search(curPattern, carSeriesHtml)
                print("foundInfo=%s" % foundInfo)
                # if foundInfo:
                infoValue = foundInfo.group("infoValue")
                print("infoValue=%s" % infoValue)
                InfoDict[eachInfoKey] = infoValue
            print("InfoDict=%s" % InfoDict)

            # if "seriesid" in InfoDict:
            carSeriesId = InfoDict["seriesid"] # 2123
            carModelDict["carSeriesId"] = carSeriesId
            # carModelDict["carSeriesName"] = InfoDict["seriesname"] # 哈弗H6
            # if "brandid" in InfoDict:
            carModelDict["carBrandId"] = InfoDict["brandid"] # 181
            # if "levelid" in InfoDict:
            carSeriesLevelId = InfoDict["levelid"] # 17
            carModelDict["carSeriesLevelId"] = carSeriesLevelId
            # if "levelname" in InfoDict:
            carModelDict["carSeriesLevelName"] = InfoDict["levelname"] # 紧凑型SUV
            # if "SeriesMinPrice" in InfoDict:
            carSeriesMinPrice = InfoDict["SeriesMinPrice"] # 9.80
            carModelDict["carSeriesMinPrice"] = self.to10KPrice(carSeriesMinPrice)
            # if "SeriesMaxPrice" in InfoDict:
            carSeriesMaxPrice = InfoDict["SeriesMaxPrice"] # 14.10
            carModelDict["carSeriesMaxPrice"] = self.to10KPrice(carSeriesMaxPrice)

            """
            <div class="series-list">
            。。。
                <li class="more-dropdown">
                    <a href="javascript:void(0);" target="_self" data-toggle="tab" class="tab-disabled" data-target="#specWrap-3">停售款 <i class="athm-iconfont athm-iconfont-arrowdown"></i></a>
                    <ul class="dropdown-con" id="haltList">
                        <li><a href="javascript:void(0);" target="_self" data-toggle="tab" data-yearid="11691">2019款</a></li>
                        ...
                        <li><a href="javascript:void(0);" target="_self" data-toggle="tab" data-yearid="3100">2011款</a></li>
                    </ul>
                </li>
            """
            haltADocGenerator = response.doc("li[class='more-dropdown'] ul[id='haltList'] li a").items()
            print("type(haltADocGenerator)=%s" % type(haltADocGenerator))
            print("haltADocGenerator=%s" % haltADocGenerator)
            haltADocList = list(haltADocGenerator)
            print("haltADocList=%s" % haltADocList)
            for curLiIdx, eachHatADoc in enumerate(haltADocList):
                print("%s [%d] %s" % ('%'*30, curLiIdx, '%'*30))
                self.processSingleHaltA(carModelDict, eachHatADoc)

            # """
            # <div class="information-summary">
            #     <dl class="information-price">
            #         ...
            #         <dd class="type">
            #             <span class="type__item">紧凑型车</span>
            # """
            # carLevelDoc = response.doc("div[class='information-summary'] dl[class='information-price'] dd[class='type'] span[class='type__item']").eq(0)
            # print("carLevelDoc=%s" % carLevelDoc)
            # carSeriesLevelName = carLevelDoc.text()
            # print("carSeriesLevelName=%s" % carSeriesLevelName)
            # carModelDict["carSeriesLevelName"] = carSeriesLevelName

            carSeriesContentDoc = response.doc("div[class='series-content']")
            # print("carSeriesContentDoc=%s" % carSeriesContentDoc)
            # carSpecWrapDoc = carSeriesContentDoc.find("div[class^='spec-wrap']")
            # carSpecWrapDoc = carSeriesContentDoc.find("div[class^='spec-wrap active']")
            carSpecWrapDocGenerator = carSeriesContentDoc.items("div[class^='spec-wrap']")
            print("carSpecWrapDocGenerator=%s" % carSpecWrapDocGenerator)
            carSpecWrapDocList = list(carSpecWrapDocGenerator)
            print("carSpecWrapDocList=%s" % carSpecWrapDocList)
            for curSpecWrapIdx, eachSpecWrapDoc in enumerate(carSpecWrapDocList):
                print("%s [%d] %s" % ('#'*30, curSpecWrapIdx, '#'*30))
                self.processSingleSpecWrapDiv(carModelDict, eachSpecWrapDoc)

    def processSingleCarDetailDiv(self, carModelDict, curCarDetailDoc):
        print("in processSingleCarDetailDiv")
        curCarModelGroupDict = copy.deepcopy(carModelDict)

        # <span class="years">2006款</span>
        modelYearDoc = curCarDetailDoc.find("span[class='years']")
        print("modelYearDoc=%s" % modelYearDoc)
        carModelYear = modelYearDoc.text()
        print("carModelYear=%s" % carModelYear)
        curCarModelGroupDict["carModelYear"] = carModelYear

        """
        <div class="modelswrap">
            <!-- 信息 start -->
            <div class="models_info">
                <dl class='models_prop'>
                    <dt>发动机：</dt>
                    <dd><span>1.3L</span><span>1.6L</span></dd>
                </dl>
                <dl class='models_prop'>
                    <dt>变速箱：</dt>
                    <dd><span>手动</span><span>自动</span></dd>
                    <dt>车身结构：</dt>
                    <dd><span>三厢</span></dd>
                </dl>
        """
        # modelsPropDdList = curCarDetailDoc.find("div[class='modelswrap'] div[class='models_info'] dl[class='models_prop'] dd")
        modelsPropDdGenerator = curCarDetailDoc.items("div[class='modelswrap'] div[class='models_info'] dl[class='models_prop'] dd")
        print("modelsPropDdGenerator=%s" % modelsPropDdGenerator)
        modelsPropDdList = list(modelsPropDdGenerator)
        print("modelsPropDdList=%s" % modelsPropDdList)
        engineValueDoc = modelsPropDdList[0]
        print("engineValueDoc=%s" % engineValueDoc)
        carModelEngine = engineValueDoc.text()
        print("carModelEngine=%s" % carModelEngine)

        gearBoxValueDoc = modelsPropDdList[1]
        print("gearBoxValueDoc=%s" % gearBoxValueDoc)
        carModelGearBox = gearBoxValueDoc.text()
        print("carModelGearBox=%s" % carModelGearBox)

        bodyStructureValueDoc = modelsPropDdList[2]
        print("bodyStructureValueDoc=%s" % bodyStructureValueDoc)
        carModelBodyStructure = bodyStructureValueDoc.text()
        print("carModelBodyStructure=%s" % carModelBodyStructure)

        curCarModelGroupDict["carModelGearBox"] = carModelGearBox # 手动自动
        curCarModelGroupDict["carModelDriveType"] = ""
        curCarModelGroupDict["carModelBodyStructure"] = carModelBodyStructure

        # curCarModelGroupDict["carModelEnvStandard"] = ""
        # carModelPower = carModelEngine
        # print("carModelPower=%s" % carModelPower)
        # curCarModelGroupDict["carModelPower"] = carModelPower
        curCarModelGroupDict["carModelEngine"] = carModelEngine # 1.3L1.6L

        carModelGroupName = "%s %s %s" % (carModelEngine, carModelGearBox, carModelBodyStructure)
        print("carModelGroupName=%s" % carModelGroupName)
        curCarModelGroupDict["carModelGroupName"] = carModelGroupName

        """
        <table class='models_tab tableline' cellspacing='0' cellpadding='0' border='0'>
            <tr>
                <td class='name_d'>
                    <div class='name'><a title='2006款 1.6L MT特别版GL' href='spec/2304/'>2006款 1.6L MT特别版GL</a></div>
                </td>
                <td class='price_d'>
                    <div class='price01'>8.18万</div>
                </td>
        """
        modelsTrDocGenerator = curCarDetailDoc.items("table[class^='models_tab'] tr")
        print("modelsTrDocGenerator=%s" % modelsTrDocGenerator)
        modelsTrDocList = list(modelsTrDocGenerator)
        print("modelsTrDocList=%s" % modelsTrDocList)
        for curTabIdx, eachModelTrDoc in enumerate(modelsTrDocList):
            print("%s [%d] %s" % ('='*30, curTabIdx, '='*30))
            self.processSingleModelsTr(curCarModelGroupDict, eachModelTrDoc)

    def processSingleModelsTr(self, curCarModelGroupDict, curModelTrDoc):
        curTrCarModeDict = copy.deepcopy(curCarModelGroupDict)
        # print("curModelTrDoc=%s" % curModelTrDoc)
        nameADoc = curModelTrDoc.find("td[class='name_d'] div[class='name'] a")
        print("nameADoc=%s" % nameADoc)
        carModelName = nameADoc.text()
        print("carModelName=%s" % carModelName)

        carModelSpecUrl = nameADoc.attr["href"]
        # bug -> wrong url:
        # https://www.autohome.com.cn/142/spec/2304/
        # need repace
        # https://www.autohome.com.cn/142/spec/2304/
        # to 
        # https://www.autohome.com.cn/spec/2304/
        foundSpecId = re.search("spec/(?P<specId>\d+)", carModelSpecUrl)
        carModelSpecId = foundSpecId.group("specId")
        print("carModelSpecId=%s" % carModelSpecId) # 2304
        carModelSpecUrl = self.genSpecUrl(carModelSpecId)
        print("carModelSpecUrl=%s" % carModelSpecUrl)

        priceDivDoc = curModelTrDoc.find("td[class='price_d'] div[class='price01']")
        print("priceDivDoc=%s" % priceDivDoc)
        carModelMsrp = priceDivDoc.text()
        print("carModelMsrp=%s" % carModelMsrp)

        curTrCarModeDict["carModelName"] = carModelName
        curTrCarModeDict["carModelSpecUrl"] = carModelSpecUrl
        curTrCarModeDict["carModelMsrp"] = carModelMsrp

        self.processSingleResult(curTrCarModeDict)

    def processSingleHaltA(self, carModelDict, curHatADoc):
        curHaltCarDict = copy.deepcopy(carModelDict)
        print("curHatADoc=%s" % curHatADoc)
        yearName = curHatADoc.text()
        print("yearName=%s" % yearName)
        yearId = curHatADoc.attr["data-yearid"]
        print("yearId=%s" % yearId)

        # getHaltSpecUrl = "https://www.autohome.com.cn/ashx/car/Spec_ListByYearId.ashx?seriesid=%s&syearid=%s&levelid=%s" % (curHaltCarDict["carSeriesId"], yearId, curHaltCarDict["carSeriesLevelId"])
        carSeriesId = curHaltCarDict["carSeriesId"]
        carSeriesLevelId = curHaltCarDict["carSeriesLevelId"]
        if carSeriesId and carSeriesLevelId:
            getHaltSpecUrl = "https://www.autohome.com.cn/ashx/car/Spec_ListByYearId.ashx?seriesid=%s&syearid=%s&levelid=%s" % (carSeriesId, yearId, carSeriesLevelId)
            # https://www.autohome.com.cn/ashx/car/Spec_ListByYearId.ashx?seriesid=2123&syearid=10379&levelid=17
            print("getHaltSpecUrl=%s" % getHaltSpecUrl)
            self.crawl(getHaltSpecUrl,
                callback=self.haltCarSpecCallback,
                save=curHaltCarDict,
            )

    def processSingleSpecWrapDiv(self, curCarModelDict, curSpecWrapDoc):
        curSpecWrapCarDict = copy.deepcopy(curCarModelDict)
        # print("curSpecWrapDoc=%s" % curSpecWrapDoc)
        """
        <!--即将上市 start-->
        <div class="spec-wrap  active" id="specWrap-1">
            
            <dl class="halt-spec">
                <dt>
                    <div class="spec-name">
                        <span>参数配置未公布</span>
                    </div>

        <dl class="halt-spec">
            <dt>
                <div class="spec-name">
                    <span>1.5升 涡轮增压 169马力 国VI</span>
                </div>
        """
        # dlDoc = curSpecWrapDoc.find("dl[class='']")
        # dlDoc = curSpecWrapDoc.find("dl")
        dlListDocGenerator = curSpecWrapDoc.items("dl")
        print("dlListDocGenerator=%s" % dlListDocGenerator)
        dlDocList = list(dlListDocGenerator)
        print("dlDocList=%s" % dlDocList)
        for curDlIdx, eachDlDoc in enumerate(dlDocList):
            print("%s [%d] %s" % ('='*30, curDlIdx, '='*30))
            self.processSingleSpecDl(curSpecWrapCarDict, eachDlDoc)
    
    def processSingleSpecDl(self, curSpecWrapCarDict, curDlDoc):
        curDlCarDict = copy.deepcopy(curSpecWrapCarDict)
        # print("curDlDoc=%s" % curDlDoc)
        """
            <dt>
                <div class="spec-name">
                    <span>1.5升 涡轮增压 169马力 国VI</span>
        """
        dtDoc = curDlDoc.find("dt")
        # print("dtDoc=%s" % dtDoc)
        groupSpecNameSpanDoc = dtDoc.find("div[class='spec-name'] span")
        print("groupSpecNameSpanDoc=%s" % groupSpecNameSpanDoc)
        carModelGroupName = ""
        if groupSpecNameSpanDoc:
            carModelGroupName = groupSpecNameSpanDoc.text()
            print("carModelGroupName=%s" % carModelGroupName)
        
        curDlCarDict["carModelGroupName"] = carModelGroupName

        # <dd data-sift1="2020款" data-sift2="国VI" data-sift3="1.5T" data-sift4="7挡双离合" class="">
        ddListDoc = curDlDoc.items("dd")
        print("ddListDoc=%s" % ddListDoc)
        for curDdIdx, eachDdDoc in enumerate(ddListDoc):
            print("%s [%d] %s" % ('-'*30, curDdIdx, '-'*30))
            self.processSingleSiftDd(curDlCarDict, eachDdDoc)
    
    def processSingleSiftDd(self, curDlCarDict, curDdDoc):
        print("in processSingleSiftDd")
        curDdCarDict = copy.deepcopy(curDlCarDict)

        curDdAttr = curDdDoc.attr
        """
        正常：
            <dd data-sift1="2020款" data-sift2="国VI" data-sift3="1.5T" data-sift4="7挡双离合" class="">
                ...
        特殊：
            无sift：
                <dd data-electricspecid="47050">
            电动的 sift位置不同：
                https://www.autohome.com.cn/5240/
                    <dd data-electricspecid="42875" data-sift1="2019款" data-sift2="100KW" data-sift3="265公里" data-sift4="单速">
            混动 sift位置也不同：
                https://www.autohome.com.cn/4460/
                    <dd data-electricspecid="37077" data-sift1="2019款" data-sift2="国V" data-sift3="2.0T" data-sift4="8挡手自一体">
        """
        # print("curDdAttr=%s" % curDdAttr)
        # carModelDataSift1 = curDdAttr["data-sift1"]
        # print("carModelDataSift1=%s" % carModelDataSift1)
        carModelYear = curDdAttr["data-sift1"]
        print("carModelYear=%s" % carModelYear)
        carModelDataSift2 = curDdAttr["data-sift2"]
        print("carModelDataSift2=%s" % carModelDataSift2)
        carModelDataSift3 = curDdAttr["data-sift3"]
        print("carModelDataSift3=%s" % carModelDataSift3)
        carModelDataSift4 = curDdAttr["data-sift4"]
        print("carModelDataSift4=%s" % carModelDataSift4)

        curDdCarDict["carModelYear"] = carModelYear
        # curDdCarDict["carModelEnvStandard"] = carModelEnvStandard
        # curDdCarDict["carModelPower"] = carModelPower
        # curDdCarDict["carModelGearBox"] = carModelGearBox
        # curDdCarDict["carModelDataSift1"] = carModelDataSift1
        curDdCarDict["carModelDataSift2"] = carModelDataSift2
        curDdCarDict["carModelDataSift3"] = carModelDataSift3
        curDdCarDict["carModelDataSift4"] = carModelDataSift4

        """
        <div class="spec-name">
            <div class="name-param">
                <p data-gcjid="41511" id="spec_41511">
                    <a href="/spec/41511/#pvareaid=3454492" class="name">2020款 1.5GDIT 自动铂金舒适版</a>
                    <span class="athm-badge athm-badge--grey is-plain">停产在售</span>
                <span class="athm-badge athm-badge--orange">特惠</span></p>
                <p><span class="type-default">前置前驱</span><span class="type-default">7挡双离合</span></p>
            </div>
        </div>
        """
        specNameDoc = curDdDoc.find("div[class='spec-name']")
        # print("specNameDoc=%s" % specNameDoc)
        specADoc = specNameDoc.find("p a[class='name']")
        # print("specADoc=%s" % specADoc)
        carModelName = specADoc.text()
        print("carModelName=%s" % carModelName) # 2020款 1.5GDIT 自动铂金舒适版
        carModelSpecUrl = specADoc.attr["href"]
        print("carModelSpecUrl=%s" % carModelSpecUrl) # https://www.autohome.com.cn/spec/41511/#pvareaid=3454492
        typeDefaultListDoc = specNameDoc.items("p span[class='type-default']")
        print("typeDefaultListDoc=%s" % typeDefaultListDoc)
        typeDefaultList = list(typeDefaultListDoc)
        print("typeDefaultList=%s" % typeDefaultList)
        carModelDriveType = ""
        carModelGearBox = ""
        if typeDefaultList:
            """
            正常：
                <p>
                    <span class="type-default">前置前驱</span>
                    <span class="type-default">7挡双离合</span>
                </p>

            特殊：
                https://www.autohome.com.cn/4605/
                <p>
                    <span class="type-default">电动</span>
                    <span class="type-default">前置前驱</span>
                    <span class="type-default">AMT（组合10挡）</span>
                </p>

                https://www.autohome.com.cn/4460/
                <p>
                    <span class="type-default">电动</span>
                    <span class="type-default">前置四驱</span>
                    <span class="type-default">8挡手自一体</span>
                </p>

                https://www.autohome.com.cn/5240/
                <p>
                    <span class="type-default">电动</span>
                    <span class="type-default">前置前驱</span>
                    <span class="type-default">电动车单速变速箱</span>
                </p>
            """
            # spanTypeDefault0 = typeDefaultList[0]
            spanTypeDefault0 = typeDefaultList[-2]
            print("spanTypeDefault0=%s" % spanTypeDefault0)
            carModelDriveType = spanTypeDefault0.text()
            print("carModelDriveType=%s" % carModelDriveType)
            # 前置前驱
            # 前置四驱
            # spanTypeDefault1 = typeDefaultList[1]
            spanTypeDefault1 = typeDefaultList[-1]
            print("spanTypeDefault1=%s" % spanTypeDefault1)
            carModelGearBox = spanTypeDefault1.text()
            print("carModelGearBox=%s" % carModelGearBox)
            # 7挡双离合
            # AMT（组合10挡）
            # 8挡手自一体
            # 电动车单速变速箱

        curDdCarDict["carModelName"] = carModelName
        if not curDdCarDict["carModelYear"]:
            foundYearType = re.search("(?P<yearType>\d{4}款)", carModelName)
            if foundYearType:
                yearType = foundYearType.group("yearType")
                print("yearType=%s" % yearType)
                carModelYear = yearType
                print("extract year=%s from modelName=%s" % (carModelYear, carModelName))
                curDdCarDict["carModelYear"] = carModelYear

        curDdCarDict["carModelSpecUrl"] = carModelSpecUrl
        curDdCarDict["carModelDriveType"] = carModelDriveType # 前置前驱
        curDdCarDict["carModelGearBox"] = carModelGearBox # 7挡双离合

        """
        <div class="spec-guidance">
            <p class="guidance-price">
                <span>10.40万</span>
                <a href="//j.autohome.com.cn/pc/carcounter?type=1&amp;specId=41511&amp;pvareaid=3454617"><i class="athm-iconpng athm-iconpng-calculator"></i></a>
            </p>
        </div>

        <div class="spec-guidance">
            <p class="guidance-price">
                <span><span>暂无</span></span>
        """
        specGuidanceDoc = curDdDoc.find("div[class='spec-guidance']")
        # print("specGuidanceDoc=%s" % specGuidanceDoc)
        guidancePriceSpanDoc = specGuidanceDoc.find("p[class='guidance-price'] span")
        # print("guidancePriceSpanDoc=%s" % guidancePriceSpanDoc)
        carModelMsrp = guidancePriceSpanDoc.text()
        print("carModelMsrp=%s" % carModelMsrp)
        curDdCarDict["carModelMsrp"] = carModelMsrp

        self.processSingleResult(curDdCarDict)

    @catch_status_code_error
    def haltCarSpecCallback(self, response):
        prevCarModelDict = response.save
        carModelDict = copy.deepcopy(prevCarModelDict)
        print("carModelDict=%s" % carModelDict)

        respJson = response.json
        print("respJson=%s" % respJson)

        """
        [
            {
                "name": "1.5升 涡轮增压 169马力",
                "speclist": [
                    {
                        "specid": 36955,
                        "specname": "2019款 红标 1.5GDIT 自动舒适版",
                        "specstate": 40,
                        "minprice": 102000,
                        "maxprice": 102000,
                        "fueltype": 1,
                        "fueltypedetail": 1,
                        "driveform": "前置前驱",
                        "drivetype": "前驱",
                        "gearbox": "7挡双离合",
                        "evflag": "",
                        "newcarflag": "",
                        "subsidy": "",
                        "paramisshow": 1,
                        "videoid": 0,
                        "link2sc": "http://www.che168.com/china/hafu/hafuh6/7_8/",
                        "price2sc": "7.58万",
                        "price": "10.20万",
                        "syear": 2019
                    }, {
                        "specid": 36956,
                        "specname": "2019款 红标 1.5GDIT 自动都市版",
                        "specstate": 40,
                        "minprice": 109000,
                        "maxprice": 109000,
                        "fueltype": 1,
                        "fueltypedetail": 1,
                        "driveform": "前置前驱",
                        "drivetype": "前驱",
                        "gearbox": "7挡双离合",
                        "evflag": "",
                        "newcarflag": "",
                        "subsidy": "",
                        "paramisshow": 1,
                        "videoid": 0,
                        "link2sc": "",
                        "price2sc": "",
                        "price": "10.90万",
                        "syear": 2019
                    },
                    ...
        """
        if respJson:
            for eachModelGroupDict in respJson:
                modelGroupName = eachModelGroupDict["name"]
                modelSpecList = eachModelGroupDict["speclist"]
                for eachModelDict in modelSpecList:
                    curCarModelDict = copy.deepcopy(carModelDict)

                    carModelYear = "%s款" % eachModelDict["syear"]
                    # carModelSpecUrl = "%s/%s" % (CarSpecPrefix, eachModelDict["specid"])
                    carModelSpecUrl = self.genSpecUrl(eachModelDict["specid"])

                    curCarModelDict["carModelGroupName"] = modelGroupName
                    curCarModelDict["carModelYear"] = carModelYear
                    # curCarModelDict["carModelEnvStandard"] = ""
                    # curCarModelDict["carModelPower"] = ""
                    curCarModelDict["carModelDriveType"] = eachModelDict["drivetype"]
                    curCarModelDict["carModelGearBox"] = eachModelDict["gearbox"]
                    curCarModelDict["carModelName"] = eachModelDict["specname"]
                    curCarModelDict["carModelSpecUrl"] = carModelSpecUrl
                    curCarModelDict["carModelMsrp"] = eachModelDict["price"]

                    self.processSingleResult(curCarModelDict)

    @catch_status_code_error
    def processCarSpecConfig(self, curCarModelDict):
        print("in processCarSpecConfig")
        carModelDict = copy.deepcopy(curCarModelDict)
        print("carModelDict=%s" % carModelDict)
        carModelSpecUrl = carModelDict["carModelSpecUrl"]
        print("carModelSpecUrl=%s" % carModelSpecUrl)
        carModelSpecId = self.extractSpecId(carModelSpecUrl)
        print("carModelSpecId=%s" % carModelSpecId)
        carModelDict["carModelSpecId"] = carModelSpecId # 43593
        carConfigSpecUrl = self.genConfigSpecUrl(carModelSpecId)
        # https://car.autohome.com.cn/config/spec/43593.html
        print("carConfigSpecUrl=%s" % carConfigSpecUrl)

        self.crawl(carConfigSpecUrl,
            # fetch_type="js",
            callback=self.carConfigSpecCallback,
            save=carModelDict,
        )

    def getItemFirstValue(self, inputContent, itemIndex):
        print("in getItemFirstValue")
        # firstItemValue = self.extractTrFirstTdValue(inputContent, itemIndex)
        firstItemValue = self.extractDictListFirstValue(inputContent, itemIndex)
        return firstItemValue

    def extractDictListFirstValue(self, paramItemDictList, itemIndex):
        """
        [
            ...,
            {
                "id": 1149,
                "name": "能源类型",
                "pnid": "1_-1",
                "valueitems": [{
                    "specid": 39893,
                    "value": "纯电动"
                }, {
                    "specid": 42875,
                    "value": "纯电动"
                }]
            }
            ...,
            {
                "id": 1292,
                "name": "<span class='hs_kw39_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
                "pnid": "1_-1",
                "valueitems": [{
                    "specid": 39893,
                    "value": "0.6"
                }, {
                    "specid": 42875,
                    "value": "0.6"
                }]
            },
            ...
            ,
            {
                "id": 1255,
                "name": "整车<span class='hs_kw36_configpl'></span>",
                "pnid": "1_-1",
                "valueitems": [{
                    "specid": 39893,
                    "value": "三<span class='hs_kw7_configpl'></span>10<span class='hs_kw1_configpl'></span>公里"
                }, {
                    "specid": 42875,
                    "value": "三<span class='hs_kw7_configpl'></span>10<span class='hs_kw1_configpl'></span>公里"
                }]
            }
        ]
        """
        paramItemDict = paramItemDictList[itemIndex]
        print("paramItemDict=%s" % paramItemDict)
        firstItemValue = self.extractValueItemsValue(paramItemDict)
        print("firstItemValue=%s" % firstItemValue)
        return firstItemValue

    def extractValueItemsValue(self, curItemDict, valueIndex=0):
        """
        {
            "id": 0,
            "name": "上市<span class='hs_kw51_configrI'></span>",
            "pnid": "1_-1",
            "valueitems": [{
                "specid": 1006466,
                "value": "2018.05"
            }, {
                "specid": 1006465,
                "value": "2018.05"
            }, {
                "specid": 1006467,
                "value": "2018.05"
            }]
        }
        """
        valueItemList = curItemDict["valueitems"]
        print("valueItemList=%s" % valueItemList)
        # firstItemDict = valueItemList[0]
        specificItemDict = valueItemList[valueIndex]
        print("specificItemDict=%s" % specificItemDict)
        # specificItemDict={'specid': 43593, 'value': "<span class='hs_kw57_configxt'></span>-<span class='hs_kw21_configxt'></span><span class='hs_kw24_configxt'></span>"}
        specificItemValue = specificItemDict["value"]
        # specificItemValue=<span class='hs_kw57_configxt'></span>-<span class='hs_kw21_configxt'></span><span class='hs_kw24_configxt'></span>
        print("specificItemValue=%s" % specificItemValue)
        return specificItemValue


    # def extractTrFirstTdValue(self, rootDoc, trNumber, isRespDoc=False):
    def extractTrFirstTdValue(self, rootDoc, trNumber):
        """
        <tr data-pnid="1_-1" id="tr_2">
            <th>
                <div id="1149"><a href="https://car.autohome.com.cn/baike/detail_7_18_1149.html#pvareaid=2042252">能源类型</a>
                </div>
            </th>
            <td style="background:#F0F3F8;">
                <div>纯电动</div>
            </td>

        <tr data-pnid="1_-1" id="tr_3">
            <th>
                <div id="0">上市<span class="hs_kw40_configxv"></span></div>
            </th>
            <td style="background:#F0F3F8;">
                <div>2019.11</div>
            </td>
            <td>
                <div>2019.11</div>
            </td>
            <td>
                <div></div>
            </td>
            <td>
                <div></div>
            </td>
        </tr>

        <tr data-pnid="1_-1" id="tr_20" style="background: rgb(255, 255, 255);">
            <th>
                <div id="1255"><a href="https://car.autohome.com.cn/baike/detail_7_18_1255.html#pvareaid=2042252">整车<span
                    class="hs_kw36_configaJ"></span></a></div>
            </th>
            <td style="background:#F0F3F8;">
                <div>三<span class="hs_kw7_configaJ"></span>10<span class="hs_kw1_configaJ"></span>公里</div>
            </td>
            <td>
                <div>三<span class="hs_kw7_configaJ"></span>10<span class="hs_kw1_configaJ"></span>公里</div>
            </td>
            <td>
                <div></div>
            </td>
            <td>
                <div></div>
            </td>
        </tr>
        """
        trQuery = "tr[id='tr_%s']" % trNumber
        # print("trQuery=%s" % trQuery)
        trDoc = rootDoc.find(trQuery)
        # print("trDoc=%s" % trDoc)
        tdDocGenerator = trDoc.items("td")
        # print("tdDocGenerator=%s" % tdDocGenerator)
        tdDocList = list(tdDocGenerator)
        # print("tdDocList=%s" % tdDocList)
        firstTdDoc = tdDocList[0]
        # print("firstTdDoc=%s" % firstTdDoc)
        firstTdDivDoc = firstTdDoc.find("div")
        print("firstTdDivDoc=%s" % firstTdDivDoc)
        # if isRespDoc:
        #     respItem = firstTdDivDoc
        # else:
        #     firstItemValue = firstTdDivDoc.text()
        #     respItem = firstItemValue
        # print("respItem=%s" % respItem)
        # return respItem
        respItemHtml = firstTdDivDoc.html()
        print("respItemHtml=%s" % respItemHtml)
        return respItemHtml
    
    # def extractWholeWarranty(self, firstDivDoc):
    def extractWholeWarranty(self, firstDivHtml):
        print("in extractWholeWarranty")
        carModelWholeWarranty = ""
        # <div>三<span class="hs_kw7_configxv"></span>10<span class="hs_kw1_configxv"></span>公里</div>
        # print("firstDivDoc=%s" % firstDivDoc)
        # carModelWholeWarranty = firstDivDoc.text() # 三10公里
        # firstDivHtml = firstDivDoc.html()
        print("firstDivHtml=%s" % firstDivHtml)
        # 三<span class="hs_kw7_configCC"></span>10<span class="hs_kw1_configCC"></span>公里
        # carWholeQualityQuarantee = re.sub("[^<>]+(?P<firstSpan><span.+?></span>)[^<>]+(?P<secondSpan><span.+?></span>)[^<>]+", )
        foundYearDistance = re.search("(?P<warrantyYear>[^<>]+)<span.+?></span>(?P<distanceNumber>[^<>]+)<span.+?></span>(?P<distanceUnit>[^<>]+)", firstDivHtml)
        if foundYearDistance:
            warrantyYear = foundYearDistance.group("warrantyYear")
            distanceNumber = foundYearDistance.group("distanceNumber")
            distanceUnit = foundYearDistance.group("distanceUnit")
            carModelWholeWarranty = "%s年或%s万%s" % (warrantyYear, distanceNumber, distanceUnit)
        else:
            # special:
            # https://car.autohome.com.cn/config/spec/46700.html
            # <div>三<span class="hs_kw58_configWh"></span></div>
            # 三<span class="hs_kw58_configOf"></span>
            foundYearNotLimitDistance = re.search("(?P<warrantyYear>[^<>]+)<span.+?></span>", firstDivHtml)
            print("foundYearNotLimitDistance=%s" % foundYearNotLimitDistance)
            if foundYearNotLimitDistance:
                warrantyYear = foundYearNotLimitDistance.group("warrantyYear")
                print("warrantyYear=%s" % warrantyYear)
                carModelWholeWarranty = "%s年不限公里" % warrantyYear
        print("carModelWholeWarranty=%s" % carModelWholeWarranty)
        return carModelWholeWarranty

    def getWholeWarranty(self, inputContent, itemIndex):
        # firstDivDoc = self.getItemFirstValue(inputContent, itemIndex, isRespDoc=True)
        # print("firstDivDoc=%s" % firstDivDoc)
        # carModelWholeWarranty = self.extractWholeWarranty(firstDivDoc)
        firstDivDocHtml = self.getItemFirstValue(inputContent, itemIndex)
        print("firstDivDocHtml=%s" % firstDivDocHtml)
        carModelWholeWarranty = self.extractWholeWarranty(firstDivDocHtml)
        return carModelWholeWarranty

    @catch_status_code_error
    def carConfigSpecCallback(self, response):
        print("in carConfigSpecCallback")
        curCarModelDict = response.save
        print("curCarModelDict=%s" % curCarModelDict)
        carModelDict = copy.deepcopy(curCarModelDict)

        configSpecHtml = response.text
        print("configSpecHtml=%s" % configSpecHtml)
        print("")

        # for debug
        return

        # # config json item index - spec table html item index = 2
        # ItemIndexDiff = 2

        # isUseSpecTableHtml = True
        # isUseConfigJson = False
        # valueContent = None
        # energyTypeIdx = 2

        # # Method 1: after run js, extract item value from spec table html
        # """
        # <table class="tbcs" id="tab_0" style="width: 932px;">
        #     <tbody>
        #         <tr>
        #             <th class="cstitle" show="1" pid="tab_0" id="nav_meto_0" colspan="5">
        #             <h3><span>基本参数</span></h3>
        #             </th>
        #         </tr>
        #         <tr data-pnid="1_-1" id="tr_0">
        # """
        # tbodyDoc = response.doc("table[id='tab_0'] tbody")
        # print("tbodyDoc=%s" % tbodyDoc)
        # valueContent = tbodyDoc
        # isUseSpecTableHtml = True
        # isUseConfigJson = False
        # energyTypeIdx = 2

        # Method 2: not run js, extract item value from config json
        # get value from config json
        # var config = {"message" ...... "returncode":"0","taskid":"8be676a3-e023-4fa9-826d-09cd42a1810c","time":"2020-08-27 20:56:17"};
        foundConfigJson = re.search("var\s*config\s*=\s*(?P<configJson>\{[^;]+\});", configSpecHtml)
        print("foundConfigJson=%s" % foundConfigJson)
        if foundConfigJson:
            configJson = foundConfigJson.group("configJson")
            print("configJson=%s" % configJson)
            # configDict = json.loads(configJson, encoding="utf-8")
            configDict = json.loads(configJson)
            print("configDict=%s" % configDict)

            # if "result" in configDict:
            configResultDict = configDict["result"]
            print("configResultDict=%s" % configResultDict)
            # if "paramtypeitems" in configResultDict:
            paramTypeItemDictList = configResultDict["paramtypeitems"]
            print("paramTypeItemDictList=%s" % paramTypeItemDictList)
            # paramTypeItemNum = len(paramTypeItemDictList)
            # print("paramTypeItemNum=%s" % paramTypeItemNum)
            basicParamDict = paramTypeItemDictList[0]
            print("basicParamDict=%s" % basicParamDict)
            basicItemDictList = basicParamDict["paramitems"]
            print("basicItemDictList=%s" % basicItemDictList)
            # print("type(basicItemDictList)=%s" % type(basicItemDictList))
            # basicItemNum = len(basicItemDictList)
            # print("basicItemNum=%s" % basicItemNum)

            # valueContent = basicItemDictList
            # isUseSpecTableHtml = False
            # isUseConfigJson = True

            # process each basic parameter
            basicItemDictLen = len(basicItemDictList)
            print("basicItemDictLen=%s" % basicItemDictLen)
            for curIdx, eachItemDict in enumerate(basicItemDictList):
                print("[%d] eachItemDict=%s" % (curIdx, eachItemDict))
                curItemId = eachItemDict["id"]
                print("curItemId=%s" % curItemId)
                curItemName = eachItemDict["name"]
                print("curItemName=%s" % curItemName)
                curItemFirstValue = self.extractValueItemsValue(eachItemDict)
                print("curItemFirstValue=%s" % curItemFirstValue)

                curIdNameKeyMapDict = None
                if curItemId != 0:
                    curIdNameKeyMapDict = self.findMappingDict(curItemId)
                else:
                    # id = 0
                    foundSpan = re.search("<span", curItemName)
                    print("foundSpan=%s" % foundSpan)
                    isSpecialName = bool(foundSpan)
                    print("isSpecialName=%s" % isSpecialName)
                    if isSpecialName:
                        # id=0 and contain '<span' special name
                        foundSuffixHour = re.search("</span>\(小时\)$", curItemName)
                        print("foundSuffixHour=%s" % foundSuffixHour)
                        isSpecialSuffixHour = bool(foundSuffixHour)
                        print("isSpecialSuffixHour=%s" % isSpecialSuffixHour)
                        if isSpecialSuffixHour:
                            prevIsQuickCharge = self.isPrevItemIsQuickCharge(curIdx, basicItemDictList)
                            print("prevIsQuickCharge=%s" % prevIsQuickCharge)
                            if prevIsQuickCharge:
                                # current is MUST 慢充时间(小时)
                                curIdNameKeyMapDict = {
                                    "id": 0,
                                    # "name": "<span class='hs_kw10_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
                                    "name": "慢充时间(小时)",
                                    "namePattern": "</span>\(小时\)$",
                                    "key": "carModelSlowCharge",
                                }
                            
                            if not curIdNameKeyMapDict:
                                prevIsActualTestEnduranceMileage = self.isPrevItemIsActualTestEnduranceMileage(curIdx, basicItemDictList)
                                print("prevIsActualTestEnduranceMileage=%s" % prevIsActualTestEnduranceMileage)
                                if prevIsActualTestEnduranceMileage:
                                    # current is MUST 实测快充时间(小时)
                                    curIdNameKeyMapDict = {
                                        "id": 0,
                                        # "name": "<span class='hs_kw22_configpl'></span><span class='hs_kw39_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
                                        "name": "实测快充时间(小时)",
                                        "namePattern": "</span>\(小时\)$",
                                        "key": "carModelActualTestQuickCharge",
                                    }

                            if not curIdNameKeyMapDict:
                                prevPrevIsActualTestEnduranceMileage = self.isPrevPrevItemIsActualTestEnduranceMileage(curIdx, basicItemDictList)
                                print("prevPrevIsActualTestEnduranceMileage=%s" % prevPrevIsActualTestEnduranceMileage)
                                if prevPrevIsActualTestEnduranceMileage:
                                    # current is MUST 实测慢充时间(小时)
                                    curIdNameKeyMapDict = {
                                        "id": 0,
                                        # "name": "<span class='hs_kw22_configpl'></span><span class='hs_kw10_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
                                        "name": "实测慢充时间(小时)",
                                        "namePattern": "</span>\(小时\)$",
                                        "key": "carModelActualTestSlowCharge",
                                    }
                        else:
                            curIdNameKeyMapDict = self.findMappingDict(0, curItemName)
                    else:
                        curIdNameKeyMapDict = self.findMappingDict(0, curItemName)

                print("curIdNameKeyMapDict=%s" % curIdNameKeyMapDict)
                if curIdNameKeyMapDict:
                    curItemKey = curIdNameKeyMapDict["key"]
                    print("curItemKey=%s" % curItemKey)
                    # processedItemValue = self.processSpecialKeyValue(curItemKey, curItemFirstValue, configSpecHtml)
                    processedItemValue = self.processSpecialKeyValue(curItemKey, curItemFirstValue, response)
                    print("processedItemValue=%s" % processedItemValue)
                    carModelDict[curItemKey] = processedItemValue
                    print("+++ added %s=%s" % (curItemKey, processedItemValue))

            print("after extract all item value: carModelDict=%s" % carModelDict)

        self.saveSingleResult(carModelDict)

        # if isUseConfigJson:
        #     energyTypeIdx += ItemIndexDiff

        # if valueContent:
        #     self.processDiffEneryTypeCar(carModelDict, valueContent, energyTypeIdx, isUseConfigJson, ItemIndexDiff)
        # else:
        #     self.saveSingleResult(carModelDict)

    # def processSpecialKeyValue(self, itemKey, itemValue, curHtml):
    def processSpecialKeyValue(self, itemKey, itemValue, response):
        print("in processSpecialKeyValue")
        print("itemKey=%s, itemValue=%s" % (itemKey, itemValue))
        if itemKey == "carModelWholeWarranty":
            print("process special carModelWholeWarranty")
            # 整车质保
            # 三<span class='hs_kw5_configJS'></span>10<span class='hs_kw0_configJS'></span>公里
            itemValue = self.extractWholeWarranty(itemValue)
            print("itemValue=%s" % itemValue)
        elif itemKey == "carModelBodyStructure":
            print("process special carModelBodyStructure value")
            # (1) https://www.autohome.com.cn/spec/46292/#pvareaid=3454492
            # 5门7座<span class='hs_kw3_configFS'></span>
            # -> 5门7座MPV
            # 
            # (2) https://www.autohome.com.cn/spec/1002900/
            # <span class='hs_kw21_configqk'></span>
            # -> 皮卡
            foundSpan = re.search("(?P<bodySpan><span.+?</span>)", itemValue)
            print("foundSpan=%s" % foundSpan)
            if foundSpan:
                bodySpan = foundSpan.group("bodySpan")
                print("bodySpan=%s" % bodySpan)
                # extract body structure
                """
                <div class="filtrate-list filtrate-list-col2">
                    <span class="title">车身结构：</span>
                    <label class="lbTxt" for="PL2$!{1 - 1}">
                        <input type="checkbox" class="selectTr_input" id="PL2$!{1 - 1}" value="MPV" name="carStruct">
                        MPV
                    </label>
                </div>
                """
                # soup = BeautifulSoup(curHtml, "html.parser")
                # # print("soup=%s" % soup)
                # # bodyStructureSpanSoup = soup.find(text="车身结构：", attrs={"class":"title"})
                # # # print("bodyStructureSpanSoup=%s" % bodyStructureSpanSoup)
                # # # emptySoup = bodyStructureSpanSoup.next_sibling
                # # # print("emptySoup=%s" % emptySoup)
                # # # siblingLabelSoup = emptySoup.next_sibling
                # # # print("siblingLabelSoup=%s" % siblingLabelSoup)
                # # parentDivSoup = bodyStructureSpanSoup.parent
                # # print("parentDivSoup=%s" % parentDivSoup)
                # # inputSoup = parentDivSoup.find("input", attrs={"type":"checkbox", "class":"selectTr_input", "name":"carStruct"})
                # carStructSoup = soup.find("input", attrs={"type":"checkbox", "class":"selectTr_input", "name":"carStruct"})
                # print("carStructSoup=%s" % carStructSoup)
                carStructDoc = response.doc("input[name=carStruct]")
                print("carStructDoc=%s" % carStructDoc)
                bodyStructureValue = carStructDoc.attr["value"]
                print("bodyStructureValue=%s" % bodyStructureValue)
                itemValue = itemValue.replace(bodySpan, bodyStructureValue)
                print("itemValue=%s" % itemValue)

        return itemValue

    def isPrevItemIsQuickCharge(self, curIdx, itemDictList):
        print("in isPrevItemIsQuickCharge")
        print("curIdx=%s" % curIdx)

        prevIsQuickCharge = False

        if curIdx > 0:
            prevIdx = curIdx - 1
            print("prevIdx=%s" % prevIdx)
            prevItemDict = itemDictList[prevIdx]
            print("prevItemDict=%s" % prevItemDict)
            prevItemId = prevItemDict["id"]
            print("prevItemId=%s" % prevItemId)
            prevItemName = prevItemDict["name"]
            print("prevItemName=%s" % prevItemName)
            """
                "id": 1292,
                # "name": "<span class='hs_kw39_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
                "name": "快充时间(小时)",
            """
            QuickChargeItemId = 1292
            if prevItemId == QuickChargeItemId:
                prevIsQuickCharge = True

        print("prevIsQuickCharge=%s" % prevIsQuickCharge)
        return prevIsQuickCharge

    def checkIsActualTestEnduranceMileage(self, prevSomeNum, curIdx, itemDictList):
        print("in checkIsActualTestEnduranceMileage")
        print("prevSomeNum=%s, curIdx=%s" % (prevSomeNum, curIdx))

        isActualTestEnduranceMileage = False

        minAllowIdx = prevSomeNum - 1

        if curIdx > minAllowIdx:
            prevSomeIdx = curIdx - prevSomeNum
            print("prevSomeIdx=%s" % prevSomeIdx)
            prevSomeItemDict = itemDictList[prevSomeIdx]
            print("prevSomeItemDict=%s" % prevSomeItemDict)
            prevSomeItemId = prevSomeItemDict["id"]
            print("prevSomeItemId=%s" % prevSomeItemId)
            prevSomeItemName = prevSomeItemDict["name"]
            print("prevSomeItemName=%s" % prevSomeItemName)

            if prevSomeItemId == 0:
                """
                    "id": 0,
                    # "name": "<span class='hs_kw22_configpl'></span>续航里程(km)",
                    "name": "实测续航里程(km)",
                    "namePattern": "</span>续航里程\(km\)$",
                    "key": "carModelActualTestEnduranceMileage",
                """
                foundActualTestEnduranceMileage = re.search("</span>续航里程\(km\)$", prevSomeItemName)
                print("foundActualTestEnduranceMileage=%s" % foundActualTestEnduranceMileage)
                if foundActualTestEnduranceMileage:
                    isActualTestEnduranceMileage = True

        print("isActualTestEnduranceMileage=%s" % isActualTestEnduranceMileage)
        return isActualTestEnduranceMileage

    def isPrevItemIsActualTestEnduranceMileage(self, curIdx, itemDictList):
        print("in isPrevItemIsActualTestEnduranceMileage")
        print("curIdx=%s" % curIdx)
        return self.checkIsActualTestEnduranceMileage(1, curIdx, itemDictList)

    def isPrevPrevItemIsActualTestEnduranceMileage(self, curIdx, itemDictList):
        print("in isPrevPrevItemIsActualTestEnduranceMileage")
        print("curIdx=%s" % curIdx)
        return self.checkIsActualTestEnduranceMileage(2, curIdx, itemDictList)

    def findMappingDict(self, itemId=0, itemName=""):
        foundMapDict = None

        paramIdNameKeyMapDict = [
            # 汽油车 参数
            # https://car.autohome.com.cn/config/spec/41572.html
            # https://car.autohome.com.cn/config/spec/1006465.html
            {
                "id": 1149,
                "name": "能源类型",
                "key": "carEnergyType",
            }, {
                "id": 1311,
                "name": "环保标准",
                "key": "carModelEnvStandard",
            }, {
                "id": 0,
                # "name": "上市<span class='hs_kw51_configvR'></span>", # 上市时间
                "name": "上市时间",
                "namePattern": "^上市",
                "key": "carModelReleaseTime",
            }, {
                "id": 1185,
                # "name": "<span class='hs_kw40_configvR'></span><span class='hs_kw15_configvR'></span>(kW)",
                "name": "最大功率(kW)",
                "key": "carModelMaxPower",
            }, {
                "id": 1186,
                # "name": "<span class='hs_kw40_configvR'></span><span class='hs_kw61_configvR'></span>(N·m)",
                "name": "最大扭矩(N·m)",
                "key": "carModelMaxTorque",
            }, {
                "id": 1150,
                "name": "发动机",
                "key": "carModelEngine",
            }, {
                "id": 1245,
                "name": "变速箱",
                "key": "carModelGearBox",
            }, {
                "id": 1148,
                "name": "长*宽*高(mm)",
                "key": "carModelSize",
            }, {
                "id": 1147,
                "name": "车身结构",
                "key": "carModelBodyStructure",
            }, {
                "id": 1246,
                "name": "最高车速(km/h)",
                "key": "carModelMaxSpeed",
            }, {
                "id": 1250,
                "name": "官方0-100km/h加速(s)",
                "key": "carModelOfficialSpeedupTime",
            }, {
                "id": 1252,
                # "name": "<span class='hs_kw26_configvR'></span>0-100km/h加速(s)",
                "name": "实测0-100km/h加速(s)",
                "key": "carModelActualTestSpeedupTime",
            }, {
                "id": 1253,
                # "name": "<span class='hs_kw26_configvR'></span>100-0km/h制动(m)",
                "name": "实测100-0km/h制动(m)",
                "key": "carModelActualTestBrakeDistance",
            }, {
                "id": 1251,
                # "name": "工信部<span class='hs_kw10_configvR'></span><span class='hs_kw43_configvR'></span>(L/100km)",
                "name": "工信部综合油耗(L/100km)",
                "key": "carModelMiitCompositeFuelConsumption",
            }, {
                "id": 1254,
                # "name": "<span class='hs_kw26_configvR'></span><span class='hs_kw43_configvR'></span>(L/100km)",
                "name": "实测油耗(L/100km)",
                "key": "carModelActualFuelConsumption",
            }, {
                "id": 1255,
                # "name": "整车<span class='hs_kw73_configvR'></span>",
                "name": "整车质保",
                "key": "carModelWholeWarranty",
            },

            # 电动车 参数
            # https://car.autohome.com.cn/config/spec/39893.html
            # https://car.autohome.com.cn/config/spec/42875.html
            {
                "id": 1291,
                "name": "工信部纯电续航里程(km)",
                "key": "carModelMiitEnduranceMileagePureElectric",
            }, {
                "id": 1292,
                # "name": "<span class='hs_kw39_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
                "name": "快充时间(小时)",
                "key": "carModelQuickCharge",
            # }, {
            #     "id": 0,
            #     # "name": "<span class='hs_kw10_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
            #     "name": "慢充时间(小时)",
            #     "namePattern": "</span>\(小时\)$",
            #     "key": "carModelSlowCharge",
            }, {
                "id": 0,
                # https://car.autohome.com.cn/config/spec/39893.html
                # {'id': 0, 'name': "<span class='hs_kw39_configMh'></span><span class='hs_kw11_configMh'></span>百分比", 'pnid': '1_-1', 'valueitems': [{'specid': 39893, 'value': '80'}, {'specid': 42875, 'value': '80'}]}
                "name": "快充电量百分比",
                "namePattern": "</span>百分比$",
                "key": "carModelQuickChargePercent",
            }, {
                "id": 0,
                "name": "电动机(Ps)",
                "key": "carModelHorsePowerElectric",
            }, {
                "id": 0,
                # "name": "<span class='hs_kw22_configpl'></span>续航里程(km)",
                "name": "实测续航里程(km)",
                "namePattern": "</span>续航里程\(km\)$",
                "key": "carModelActualTestEnduranceMileage",
            # }, {
            #     "id": 0,
            #     # "name": "<span class='hs_kw22_configpl'></span><span class='hs_kw39_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
            #     "name": "实测快充时间(小时)",
            #     "namePattern": "</span>\(小时\)$",
            #     "key": "carModelActualTestQuickCharge",
            # }, {
            #     "id": 0,
            #     # "name": "<span class='hs_kw22_configpl'></span><span class='hs_kw10_configpl'></span><span class='hs_kw40_configpl'></span>(小时)",
            #     "name": "实测慢充时间(小时)",
            #     "namePattern": "</span>\(小时\)$",
            #     "key": "carModelActualTestSlowCharge",
            }
        ]

        isItemZero = itemId == 0
        print("isItemZero=%s" % isItemZero)

        foundSpan = re.search("<span", itemName)
        print("foundSpan=%s" % foundSpan)
        isSpecialName = bool(foundSpan)
        print("isSpecialName=%s" % isSpecialName)
        isNotSpecialName = not isSpecialName
        print("isNotSpecialName=%s" % isNotSpecialName)

        if not isItemZero:
            for eachMapDict in paramIdNameKeyMapDict:
                eachItemId = eachMapDict["id"]
                if eachItemId == itemId:
                    foundMapDict = eachMapDict
                    break

        if not foundMapDict:
            if itemName and isNotSpecialName:
                for eachMapDict in paramIdNameKeyMapDict:
                    eachItemName = eachMapDict["name"]
                    if eachItemName == itemName:
                        foundMapDict = eachMapDict
                        break

        if not foundMapDict:
            if (isItemZero and isSpecialName):
                for eachMapDict in paramIdNameKeyMapDict:
                    if "namePattern" in eachMapDict:
                        eachItemNamePattern = eachMapDict["namePattern"]
                        print("eachItemNamePattern=%s" % eachItemNamePattern)
                        foundMatchName = re.search(eachItemNamePattern, itemName)
                        print("foundMatchName=%s" % foundMatchName)
                        if foundMatchName:
                            foundMapDict = eachMapDict
                            break
        print("foundMapDict=%s from id=%s, name=%s" % (foundMapDict, itemId, itemName))
        return foundMapDict

    def processDiffEneryTypeCar(self, carModelDict, valueContent, energyTypeIdx, isUseConfigJson, ItemIndexDiff):
        carEnergyType = self.getItemFirstValue(valueContent, energyTypeIdx)
        # 纯电动 / 汽油 / 插电式混合动力 / 油电混合
        carModelDict["carEnergyType"] = carEnergyType

        if carEnergyType == "汽油":
            # https://car.autohome.com.cn/config/spec/43593.html
            # https://car.autohome.com.cn/config/spec/41572.html

            # self.processGasolineCar(valueContent, carModelDict)

            # https://car.autohome.com.cn/config/spec/1006466.html

            gasolineCarKeyIdxMapDict = {
                "carModelEnvStandard" : 3,
                "carModelReleaseTime" : 4,
                "carModelMaxPower" : 5,
                "carModelMaxTorque" : 6,
                "carModelEngine" : 7,
                "carModelGearBox" : 8,
                "carModelSize" : 9,
                "carModelBodyStructure" : 10,
                "carModelMaxSpeed" : 11,
                "carModelOfficialSpeedupTime" : 12,
                "carModelActualTestSpeedupTime" : 13,
                "carModelActualTestBrakeDistance" : 14,
                "carModelMiitCompositeFuelConsumption" : 15,
                "carModelActualFuelConsumption" : 16,
            }
            wholeWarrantyIdx = 17

            if isUseConfigJson:
                for eachKey in gasolineCarKeyIdxMapDict.keys():
                    gasolineCarKeyIdxMapDict[eachKey] += ItemIndexDiff
                wholeWarrantyIdx += ItemIndexDiff

            self.processSingleEneryTypeCar(gasolineCarKeyIdxMapDict, valueContent, wholeWarrantyIdx, carModelDict)

        elif carEnergyType == "纯电动":
            # https://car.autohome.com.cn/config/spec/42875.html

            # self.processPureElectricCar(valueContent, carModelDict)

            pureElectricCarKeyIdxMapDict = {
                "carModelReleaseTime": 3,
                "carModelMiitEnduranceMileagePureElectric": 4,
                "carModelQuickCharge": 5,
                "carModelSlowCharge": 6,
                "carModelQuickChargePercent": 7,
                "carModelMaxPower": 8,
                "carModelMaxTorque": 9,
                "carModelHorsePowerElectric": 10,
                "carModelSize": 11,
                "carModelBodyStructure": 12,
                "carModelMaxSpeed": 13,
                "carModelOfficialSpeedupTime": 14,
                "carModelActualTestSpeedupTime": 15,
                "carModelActualTestBrakeDistance": 16,
                "carModelActualTestEnduranceMileage": 17,
                "carModelActualTestQuickCharge": 18,
                "carModelActualTestSlowCharge": 19,
            }
            wholeWarrantyIdx = 20

            if isUseConfigJson:
                for eachKey in pureElectricCarKeyIdxMapDict.keys():
                    pureElectricCarKeyIdxMapDict[eachKey] += ItemIndexDiff
                wholeWarrantyIdx += ItemIndexDiff

            self.processSingleEneryTypeCar(pureElectricCarKeyIdxMapDict, valueContent, wholeWarrantyIdx, carModelDict)

        elif carEnergyType == "插电式混合动力":
            # https://car.autohome.com.cn/config/series/4460.html

            # self.processPhevCar(valueContent, carModelDict)

            phevCarKeyIdxMapDict = {
                "carModelEnvStandard": 3,
                "carModelReleaseTime": 4,
                "carModelMiitEnduranceMileagePureElectric": 5,
                "carModelQuickCharge": 6,
                "carModelSlowCharge": 7,
                "carModelQuickChargePercent": 8,
                "carModelMaxPower": 9,
                "carModelMaxTorque": 10,
                "carModelEngine": 11,
                "carModelHorsePowerElectric": 12,
                "carModelGearBox": 13,
                "carModelSize": 14,
                "carModelBodyStructure": 15,
                "carModelMaxSpeed": 16,
                "carModelOfficialSpeedupTime": 17,
                "carModelActualTestSpeedupTime": 18,
                "carModelActualTestBrakeDistance": 19,
                "carModelActualTestEnduranceMileage": 20,
                "carModelActualTestQuickCharge": 21,
                "carModelActualTestSlowCharge": 22,
                "carModelMiitCompositeFuelConsumption": 23,
                "carModelActualFuelConsumption": 24,
            }
            wholeWarrantyIdx = 25

            if isUseConfigJson:
                for eachKey in phevCarKeyIdxMapDict.keys():
                    phevCarKeyIdxMapDict[eachKey] += ItemIndexDiff
                wholeWarrantyIdx += ItemIndexDiff

            self.processSingleEneryTypeCar(phevCarKeyIdxMapDict, valueContent, wholeWarrantyIdx, carModelDict)

        elif carEnergyType == "油电混合":
            # https://car.autohome.com.cn/config/spec/35507.html

            # self.processHevCar(valueContent, carModelDict)

            hevCarKeyIdxMapDict = {
                "carModelEnvStandard": 3,
                "carModelReleaseTime": 4,
                "carModelMaxPower": 5,
                "carModelMaxTorque": 6,
                "carModelEngine": 7,
                "carModelHorsePowerElectric": 8,
                "carModelGearBox": 9,
                "carModelSize": 10,
                "carModelBodyStructure": 11,
                "carModelMaxSpeed": 12,
                "carModelOfficialSpeedupTime": 13,
                "carModelActualTestSpeedupTime": 14,
                "carModelActualTestBrakeDistance": 15,
                "carModelMiitCompositeFuelConsumption": 16,
                "carModelActualFuelConsumption": 17,
            }
            wholeWarrantyIdx = 18

            if isUseConfigJson:
                for eachKey in hevCarKeyIdxMapDict.keys():
                    hevCarKeyIdxMapDict[eachKey] += ItemIndexDiff
                wholeWarrantyIdx += ItemIndexDiff

            self.processSingleEneryTypeCar(hevCarKeyIdxMapDict, valueContent, wholeWarrantyIdx, carModelDict)
        else:
            errMsg = "TODO: add support %s!" % carEnergyType
            raise Exception(errMsg)

    def processSingleEneryTypeCar(self, keyIdxMapDict, valueContent, wholeWarrantyIdx, carModelDict):
        keyList = keyIdxMapDict.keys()
        keyListLen = len(keyList)
        print("keyListLen=%s" % keyListLen)
        for eachItemKey in keyList:
            print("eachItemKey=%s" % eachItemKey)
            eachItemIndex = keyIdxMapDict[eachItemKey]
            print("eachItemIndex=%s" % eachItemIndex)
            eachItemValue = self.getItemFirstValue(valueContent, eachItemIndex)
            print("eachItemValue=%s" % eachItemValue)
            carModelDict[eachItemKey] = eachItemValue

        # 整车质保
        carModelWholeWarranty = self.getWholeWarranty(valueContent, wholeWarrantyIdx) # 三年或10万公里
        print("carModelWholeWarranty=%s" % carModelWholeWarranty)
        carModelDict["carModelWholeWarranty"] = carModelWholeWarranty

        self.saveSingleResult(carModelDict)

    # def processGasolineCar(self, valueContent, carModelDict):
    #     # 汽油

    #     # https://car.autohome.com.cn/config/spec/43593.html
    #     # https://car.autohome.com.cn/config/spec/41572.html

    #     # 环保标准
    #     carModelEnvStandard = self.getItemFirstValue(valueContent, 3) # 国VI
    #     carModelDict["carModelEnvStandard"] = carModelEnvStandard

    #     # 上市时间
    #     carModelReleaseTime = self.getItemFirstValue(valueContent, 4) # 2020.04
    #     carModelDict["carModelReleaseTime"] = carModelReleaseTime

    #     # 最大功率(kW)
    #     carModelMaxPower = self.getItemFirstValue(valueContent, 5) # 110
    #     carModelDict["carModelMaxPower"] = carModelMaxPower

    #     # 最大扭矩(N·m)
    #     carModelMaxTorque = self.getItemFirstValue(valueContent, 6) # 250
    #     carModelDict["carModelMaxTorque"] = carModelMaxTorque

    #     # 发动机
    #     carModelEngine = self.getItemFirstValue(valueContent, 7) # 1.4T 150马力 L4
    #     carModelDict["carModelEngine"] = carModelEngine

    #     # 变速箱
    #     carModelGearBox = self.getItemFirstValue(valueContent, 8) # 7挡双离合
    #     carModelDict["carModelGearBox"] = carModelGearBox

    #     # 长*宽*高(mm)
    #     carModelSize = self.getItemFirstValue(valueContent, 9) # 4312*1785*1426
    #     carModelDict["carModelSize"] = carModelSize

    #     # 车身结构
    #     carModelBodyStructure = self.getItemFirstValue(valueContent, 10) # 5门5座两厢车
    #     carModelDict["carModelBodyStructure"] = carModelBodyStructure

    #     # 最高车速(km/h)
    #     carModelMaxSpeed = self.getItemFirstValue(valueContent, 11) # 200
    #     carModelDict["carModelMaxSpeed"] = carModelMaxSpeed

    #     # 官方0-100km/h加速(s)
    #     carModelOfficialSpeedupTime = self.getItemFirstValue(valueContent, 12) # 8.4
    #     carModelDict["carModelOfficialSpeedupTime"] = carModelOfficialSpeedupTime

    #     # 实测0-100km/h加速(s)
    #     carModelActualTestSpeedupTime = self.getItemFirstValue(valueContent, 13) # -
    #     carModelDict["carModelActualTestSpeedupTime"] = carModelActualTestSpeedupTime

    #     # 实测100-0km/h制动(m)
    #     carModelActualTestBrakeDistance = self.getItemFirstValue(valueContent, 14) # -
    #     carModelDict["carModelActualTestBrakeDistance"] = carModelActualTestBrakeDistance

    #     # 工信部综合油耗(L/100km)
    #     carModelMiitCompositeFuelConsumption = self.getItemFirstValue(valueContent, 15) # 5.8
    #     carModelDict["carModelMiitCompositeFuelConsumption"] = carModelMiitCompositeFuelConsumption

    #     # 实测油耗(L/100km)
    #     carModelActualFuelConsumption = self.getItemFirstValue(valueContent, 16) # -
    #     carModelDict["carModelActualFuelConsumption"] = carModelActualFuelConsumption

    #     self.saveSingleResult(carModelDict)

    # def processPureElectricCar(self, valueContent, carModelDict):
    #     # 纯电动

    #     # https://car.autohome.com.cn/config/spec/42875.html

    #     # 上市时间
    #     carModelReleaseTime = self.getItemFirstValue(valueContent, 3) # 2019.11
    #     carModelDict["carModelReleaseTime"] = carModelReleaseTime

    #     # 工信部纯电续航里程(km)
    #     carModelMiitEnduranceMileagePureElectric = self.getItemFirstValue(valueContent, 4) # 265
    #     carModelDict["carModelMiitEnduranceMileagePureElectric"] = carModelMiitEnduranceMileagePureElectric

    #     # 快充时间(小时)
    #     carModelQuickCharge = self.getItemFirstValue(valueContent, 5) # 0.6
    #     carModelDict["carModelQuickCharge"] = carModelQuickCharge

    #     # 慢充时间(小时)
    #     carModelSlowCharge = self.getItemFirstValue(valueContent, 6) # 17
    #     carModelDict["carModelSlowCharge"] = carModelSlowCharge

    #     # 快充电量百分比
    #     carModelQuickChargePercent = self.getItemFirstValue(valueContent, 7) # 80
    #     carModelDict["carModelQuickChargePercent"] = carModelQuickChargePercent

    #     # 最大功率(kW)
    #     carModelMaxPower = self.getItemFirstValue(valueContent, 8) # 100
    #     carModelDict["carModelMaxPower"] = carModelMaxPower

    #     # 最大扭矩(N·m)
    #     carModelMaxTorque = self.getItemFirstValue(valueContent, 9) # 290
    #     carModelDict["carModelMaxTorque"] = carModelMaxTorque

    #     # 电动机(Ps)
    #     carModelHorsePowerElectric = self.getItemFirstValue(valueContent, 10) # 136
    #     carModelDict["carModelHorsePowerElectric"] = carModelHorsePowerElectric

    #     # 长*宽*高(mm)
    #     carModelSize = self.getItemFirstValue(valueContent, 11) # 4237*1785*1548
    #     carModelDict["carModelSize"] = carModelSize

    #     # 车身结构
    #     carModelBodyStructure = self.getItemFirstValue(valueContent, 12) # 5门5座SUV
    #     carModelDict["carModelBodyStructure"] = carModelBodyStructure

    #     # 最高车速(km/h)
    #     carModelMaxSpeed = self.getItemFirstValue(valueContent, 13) # 150
    #     carModelDict["carModelMaxSpeed"] = carModelMaxSpeed

    #     # 官方0-100km/h加速(s)
    #     carModelOfficialSpeedupTime = self.getItemFirstValue(valueContent, 14) # -
    #     carModelDict["carModelOfficialSpeedupTime"] = carModelOfficialSpeedupTime

    #     # 实测0-100km/h加速(s)
    #     carModelActualTestSpeedupTime = self.getItemFirstValue(valueContent, 15) # -
    #     carModelDict["carModelActualTestSpeedupTime"] = carModelActualTestSpeedupTime

    #     # 实测100-0km/h制动(m)
    #     carModelActualTestBrakeDistance = self.getItemFirstValue(valueContent, 16) # -
    #     carModelDict["carModelActualTestBrakeDistance"] = carModelActualTestBrakeDistance

    #     # 实测续航里程(km)
    #     carModelActualTestEnduranceMileage = self.getItemFirstValue(valueContent, 17) # -
    #     carModelDict["carModelActualTestEnduranceMileage"] = carModelActualTestEnduranceMileage

    #     # 实测快充时间(小时)
    #     carModelActualTestQuickCharge = self.getItemFirstValue(valueContent, 18) # -
    #     carModelDict["carModelActualTestQuickCharge"] = carModelActualTestQuickCharge

    #     # 实测慢充时间(小时)
    #     carModelActualTestSlowCharge = self.getItemFirstValue(valueContent, 19) # -
    #     carModelDict["carModelActualTestSlowCharge"] = carModelActualTestSlowCharge

    #     # 整车质保
    #     carModelWholeWarranty = self.getWholeWarranty(valueContent, 20) # 三年或10万公里
    #     carModelDict["carModelWholeWarranty"] = carModelWholeWarranty

    #     self.saveSingleResult(carModelDict)

    # def processPhevCar(self, valueContent, carModelDict):
    #     # 插电式混合动力 = PHEV = Plug-in Hybrid Electric vehicle

    #     # https://car.autohome.com.cn/config/series/4460.html

    #     # 环保标准
    #     carModelEnvStandard = self.getItemFirstValue(valueContent, 3) # 国V
    #     carModelDict["carModelEnvStandard"] = carModelEnvStandard

    #     # 上市时间
    #     carModelReleaseTime = self.getItemFirstValue(valueContent, 4) # 2018.11
    #     carModelDict["carModelReleaseTime"] = carModelReleaseTime

    #     # 工信部纯电续航里程(km)
    #     carModelMiitEnduranceMileagePureElectric = self.getItemFirstValue(valueContent, 5) # 56
    #     carModelDict["carModelMiitEnduranceMileagePureElectric"] = carModelMiitEnduranceMileagePureElectric

    #     # 快充时间(小时)
    #     carModelQuickCharge = self.getItemFirstValue(valueContent, 6) # 2.5
    #     carModelDict["carModelQuickCharge"] = carModelQuickCharge

    #     # 慢充时间(小时)
    #     carModelSlowCharge = self.getItemFirstValue(valueContent, 7) # 10.8
    #     carModelDict["carModelSlowCharge"] = carModelSlowCharge

    #     # 快充电量百分比
    #     carModelQuickChargePercent = self.getItemFirstValue(valueContent, 8) # -
    #     carModelDict["carModelQuickChargePercent"] = carModelQuickChargePercent

    #     # 最大功率(kW)
    #     carModelMaxPower = self.getItemFirstValue(valueContent, 9) # 270
    #     carModelDict["carModelMaxPower"] = carModelMaxPower

    #     # 最大扭矩(N·m)
    #     carModelMaxTorque = self.getItemFirstValue(valueContent, 10) # 700
    #     carModelDict["carModelMaxTorque"] = carModelMaxTorque

    #     # 发动机
    #     carModelEngine = self.getItemFirstValue(valueContent, 11) # 2.0T 252马力 L4
    #     carModelDict["carModelEngine"] = carModelEngine

    #     # 电动机(Ps)
    #     carModelHorsePowerElectric = self.getItemFirstValue(valueContent, 12) # 128
    #     carModelDict["carModelHorsePowerElectric"] = carModelHorsePowerElectric

    #     # 变速箱
    #     carModelGearBox = self.getItemFirstValue(valueContent, 13) # 8挡手自一体
    #     carModelDict["carModelGearBox"] = carModelGearBox

    #     # 长*宽*高(mm)
    #     carModelSize = self.getItemFirstValue(valueContent, 14) # 5071*1968*1716
    #     carModelDict["carModelSize"] = carModelSize

    #     # 车身结构
    #     carModelBodyStructure = self.getItemFirstValue(valueContent, 15) # 5门5座SUV
    #     carModelDict["carModelBodyStructure"] = carModelBodyStructure

    #     # 最高车速(km/h)
    #     carModelMaxSpeed = self.getItemFirstValue(valueContent, 16) # 228
    #     carModelDict["carModelMaxSpeed"] = carModelMaxSpeed

    #     # 官方0-100km/h加速(s)
    #     carModelOfficialSpeedupTime = self.getItemFirstValue(valueContent, 17) # 5.9
    #     carModelDict["carModelOfficialSpeedupTime"] = carModelOfficialSpeedupTime

    #     # 实测0-100km/h加速(s)
    #     carModelActualTestSpeedupTime = self.getItemFirstValue(valueContent, 18) # -
    #     carModelDict["carModelActualTestSpeedupTime"] = carModelActualTestSpeedupTime

    #     # 实测100-0km/h制动(m)
    #     carModelActualTestBrakeDistance = self.getItemFirstValue(valueContent, 19) # -
    #     carModelDict["carModelActualTestBrakeDistance"] = carModelActualTestBrakeDistance

    #     # 实测续航里程(km)
    #     carModelActualTestEnduranceMileage = self.getItemFirstValue(valueContent, 20) # -
    #     carModelDict["carModelActualTestEnduranceMileage"] = carModelActualTestEnduranceMileage

    #     # 实测快充时间(小时)
    #     carModelActualTestQuickCharge = self.getItemFirstValue(valueContent, 21) # -
    #     carModelDict["carModelActualTestQuickCharge"] = carModelActualTestQuickCharge

    #     # 实测慢充时间(小时)
    #     carModelActualTestSlowCharge = self.getItemFirstValue(valueContent, 22) # -
    #     carModelDict["carModelActualTestSlowCharge"] = carModelActualTestSlowCharge

    #     # 工信部综合油耗(L/100km)
    #     carModelMiitCompositeFuelConsumption = self.getItemFirstValue(valueContent, 23) # 2.4
    #     carModelDict["carModelMiitCompositeFuelConsumption"] = carModelMiitCompositeFuelConsumption

    #     # 实测油耗(L/100km)
    #     carModelActualFuelConsumption = self.getItemFirstValue(valueContent, 24) # -
    #     carModelDict["carModelActualFuelConsumption"] = carModelActualFuelConsumption

    #     # 整车质保
    #     carModelWholeWarranty = self.getWholeWarranty(valueContent, 25) # 三年或10万公里
    #     carModelDict["carModelWholeWarranty"] = carModelWholeWarranty

    #     self.saveSingleResult(carModelDict)

    # def processHevCar(self, valueContent, carModelDict):
    #     # 混合电动汽车=HEV=Hybrid Electric Vehicle

    #     # https://car.autohome.com.cn/config/spec/35507.html

    #     # 环保标准
    #     carModelEnvStandard = self.getItemFirstValue(valueContent, 3) # 国IV(国V)
    #     carModelDict["carModelEnvStandard"] = carModelEnvStandard

    #     # 上市时间
    #     carModelReleaseTime = self.getItemFirstValue(valueContent, 4) # 2018.08
    #     carModelDict["carModelReleaseTime"] = carModelReleaseTime

    #     # 最大功率(kW)
    #     carModelMaxPower = self.getItemFirstValue(valueContent, 5) # 100
    #     carModelDict["carModelMaxPower"] = carModelMaxPower

    #     # 最大扭矩(N·m)
    #     carModelMaxTorque = self.getItemFirstValue(valueContent, 6) # -
    #     carModelDict["carModelMaxTorque"] = carModelMaxTorque

    #     # 发动机
    #     carModelEngine = self.getItemFirstValue(valueContent, 7) # 1.8L 99马力 L4
    #     carModelDict["carModelEngine"] = carModelEngine

    #     # 电动机(Ps)
    #     carModelHorsePowerElectric = self.getItemFirstValue(valueContent, 8) # 82
    #     carModelDict["carModelHorsePowerElectric"] = carModelHorsePowerElectric

    #     # 变速箱
    #     carModelGearBox = self.getItemFirstValue(valueContent, 9) # E-CVT无级变速
    #     carModelDict["carModelGearBox"] = carModelGearBox

    #     # 长*宽*高(mm)
    #     carModelSize = self.getItemFirstValue(valueContent, 10) # 4360*1765*1455
    #     carModelDict["carModelSize"] = carModelSize

    #     # 车身结构
    #     carModelBodyStructure = self.getItemFirstValue(valueContent, 11) # 5门5座SUV
    #     carModelDict["carModelBodyStructure"] = carModelBodyStructure

    #     # 最高车速(km/h)
    #     carModelMaxSpeed = self.getItemFirstValue(valueContent, 12) # -
    #     carModelDict["carModelMaxSpeed"] = carModelMaxSpeed

    #     # 官方0-100km/h加速(s)
    #     carModelOfficialSpeedupTime = self.getItemFirstValue(valueContent, 13) # -
    #     carModelDict["carModelOfficialSpeedupTime"] = carModelOfficialSpeedupTime

    #     # 实测0-100km/h加速(s)
    #     carModelActualTestSpeedupTime = self.getItemFirstValue(valueContent, 14) # -
    #     carModelDict["carModelActualTestSpeedupTime"] = carModelActualTestSpeedupTime

    #     # 实测100-0km/h制动(m)
    #     carModelActualTestBrakeDistance = self.getItemFirstValue(valueContent, 15) # -
    #     carModelDict["carModelActualTestBrakeDistance"] = carModelActualTestBrakeDistance

    #     # 工信部综合油耗(L/100km)
    #     carModelMiitCompositeFuelConsumption = self.getItemFirstValue(valueContent, 16) # 4.6
    #     carModelDict["carModelMiitCompositeFuelConsumption"] = carModelMiitCompositeFuelConsumption

    #     # 实测油耗(L/100km)
    #     carModelActualFuelConsumption = self.getItemFirstValue(valueContent, 17) # -
    #     carModelDict["carModelActualFuelConsumption"] = carModelActualFuelConsumption

    #     # 整车质保
    #     carModelWholeWarranty = self.getWholeWarranty(valueContent, 18) # 六年或15万公里
    #     carModelDict["carModelWholeWarranty"] = carModelWholeWarranty

    #     self.saveSingleResult(carModelDict)

    def processSingleResult(self, curCarModelDict):
        print("in processSingleResult")
        self.processCarSpecConfig(curCarModelDict)

        # self.saveSingleResult(curCarModelDict)

    def saveSingleResult(self, curCarModelDict):
        carModelDict = copy.deepcopy(curCarModelDict)
        # print("before filter: carModelDict=%s" % carModelDict)
        # process
        for curKey, curValue in carModelDict.items():
            print("curKey=%s, curValue=%s" % (curKey, curValue))
            if curValue is None:
                carModelDict[curKey] = ""
            elif curValue == "-":
                # '-' -> ''
                carModelDict[curKey] = ""
            elif "暂无" in curValue:
                # '暂无 暂无 暂无', '暂无' -> ''
                carModelDict[curKey] = ""
        # print("after filter: carModelDict=%s" % carModelDict)
        """
        插电式混合动力
            https://www.autohome.com.cn/spec/37077/
                {
                    "carBrandId": "33",
                    "carBrandLogoUrl": "https://car2.autoimg.cn/cardfs/series/g26/M0B/AE/B3/100x100_f40_autohomecar__wKgHEVs9u5WAV441AAAKdxZGE4U148.png",
                    "carBrandName": "奥迪",
                    "carEnergyType": "插电式混合动力",
                    "carMerchantName": "奥迪(进口)",
                    "carMerchantUrl": "https://car.autohome.com.cn/price/brand-33-79.html#pvareaid=2042363",
                    "carModelActualFuelConsumption": "",
                    "carModelActualTestBrakeDistance": "",
                    "carModelActualTestEnduranceMileage": "",
                    "carModelActualTestQuickCharge": "",
                    "carModelActualTestSlowCharge": "",
                    "carModelActualTestSpeedupTime": "",
                    "carModelBodyStructure": "5门5座SUV",
                    "carModelDataSift2": "国V",
                    "carModelDataSift3": "2.0T",
                    "carModelDataSift4": "8挡手自一体",
                    "carModelDriveType": "前置四驱",
                    "carModelEngine": "2.0T 252马力 L4",
                    "carModelEnvStandard": "国V",
                    "carModelGearBox": "8挡手自一体",
                    "carModelGroupName": "2.0升 涡轮增压 252马力 国V",
                    "carModelHorsePowerElectric": "128",
                    "carModelMaxPower": "270",
                    "carModelMaxSpeed": "228",
                    "carModelMaxTorque": "700",
                    "carModelMiitCompositeFuelConsumption": "2.4",
                    "carModelMiitEnduranceMileagePureElectric": "56",
                    "carModelMsrp": "79.08万",
                    "carModelName": "2019款 55 e-tron",
                    "carModelOfficialSpeedupTime": "5.9",
                    "carModelQuickCharge": "2.5",
                    "carModelQuickChargePercent": "",
                    "carModelReleaseTime": "2018.11",
                    "carModelSize": "5071*1968*1716",
                    "carModelSlowCharge": "10.8",
                    "carModelSpecId": "37077",
                    "carModelSpecUrl": "https://www.autohome.com.cn/spec/37077/#pvareaid=3454492",
                    "carModelWholeWarranty": "三年或10万公里",
                    "carModelYear": "2019款",
                    "carSeriesId": "4460",
                    "carSeriesLevelId": "19",
                    "carSeriesLevelName": "中大型SUV",
                    "carSeriesMainImgUrl": "https://car3.autoimg.cn/cardfs/product/g3/M01/45/A0/380x285_0_q87_autohomecar__ChcCRVwuElKAXUwcAAfU0sgxuiw392.jpg",
                    "carSeriesMaxPrice": "79.08万",
                    "carSeriesMinPrice": "79.08万",
                    "carSeriesMsrp": "79.08-79.08万",
                    "carSeriesMsrpUrl": "https://www.autohome.com.cn/4460/price.html#pvareaid=101446",
                    "carSeriesName": "奥迪Q7新能源",
                    "carSeriesUrl": "https://www.autohome.com.cn/4460/#levelsource=000000000_0&pvareaid=101594"
                }

        汽油
            https://www.autohome.com.cn/spec/43593/
                {
                    "carBrandId": "33",
                    "carBrandLogoUrl": "https://car2.autoimg.cn/cardfs/series/g26/M0B/AE/B3/100x100_f40_autohomecar__wKgHEVs9u5WAV441AAAKdxZGE4U148.png",
                    "carBrandName": "奥迪",
                    "carEnergyType": "汽油",
                    "carMerchantName": "一汽-大众奥迪",
                    "carMerchantUrl": "https://car.autohome.com.cn/price/brand-33-9.html#pvareaid=2042363",
                    "carModelActualFuelConsumption": "",
                    "carModelActualTestBrakeDistance": "",
                    "carModelActualTestSpeedupTime": "",
                    "carModelBodyStructure": "5门5座两厢车",
                    "carModelDataSift2": "国VI",
                    "carModelDataSift3": "1.4T",
                    "carModelDataSift4": "7挡双离合",
                    "carModelDriveType": "前置前驱",
                    "carModelEngine": "1.4T 150马力 L4",
                    "carModelEnvStandard": "国VI",
                    "carModelGearBox": "7挡双离合",
                    "carModelGroupName": "1.4升 涡轮增压 150马力 国VI",
                    "carModelMaxPower": "110",
                    "carModelMaxSpeed": "200",
                    "carModelMaxTorque": "250",
                    "carModelMiitCompositeFuelConsumption": "5.8",
                    "carModelMsrp": "19.32万",
                    "carModelName": "2020款 改款 Sportback 35 TFSI 进取型 国VI",
                    "carModelOfficialSpeedupTime": "8.4",
                    "carModelReleaseTime": "2020.04",
                    "carModelSize": "4312*1785*1426",
                    "carModelSpecId": "43593",
                    "carModelSpecUrl": "https://www.autohome.com.cn/spec/43593/#pvareaid=3454492",
                    "carModelWholeWarranty": "三年或10万公里",
                    "carModelYear": "2020款",
                    "carSeriesId": "3170",
                    "carSeriesLevelId": "3",
                    "carSeriesLevelName": "紧凑型车",
                    "carSeriesMainImgUrl": "https://car3.autoimg.cn/cardfs/product/g27/M0A/C9/C8/380x285_0_q87_autohomecar__ChsEnV2uZRCAIMoIAAcQmM2ogcg307.jpg",
                    "carSeriesMaxPrice": "23.46万",
                    "carSeriesMinPrice": "19.32万",
                    "carSeriesMsrp": "19.32-23.46万",
                    "carSeriesMsrpUrl": "https://www.autohome.com.cn/3170/price.html#pvareaid=101446",
                    "carSeriesName": "奥迪A3",
                    "carSeriesUrl": "https://www.autohome.com.cn/3170/#levelsource=000000000_0&pvareaid=101594"
                }

            https://car.autohome.com.cn/config/spec/16147.html
                {
                    "carBrandId": "91",
                    "carBrandLogoUrl": "https://car3.autoimg.cn/cardfs/series/g26/M05/AE/94/100x100_f40_autohomecar__wKgHEVs9tm6ASWlTAAAUz_2mWTY720.png",
                    "carBrandName": "红旗",
                    "carEnergyType": "汽油",
                    "carMerchantName": "一汽红旗",
                    "carMerchantUrl": "https://car.autohome.com.cn/price/brand-91-190.html#pvareaid=2042363",
                    "carModelActualFuelConsumption": "",
                    "carModelActualTestBrakeDistance": "",
                    "carModelActualTestSpeedupTime": "",
                    "carModelBodyStructure": "4门5座三厢车",
                    "carModelDriveType": "后驱",
                    "carModelEngine": "2.0T 204马力 L4",
                    "carModelEnvStandard": "国IV(国V)",
                    "carModelGearBox": "6挡手自一体",
                    "carModelGroupName": "2.0升 涡轮增压 204马力",
                    "carModelMaxPower": "150",
                    "carModelMaxSpeed": "",
                    "carModelMaxTorque": "260",
                    "carModelMiitCompositeFuelConsumption": "9.8",
                    "carModelMsrp": "37.98万",
                    "carModelName": "2013款 2.0T 尊贵型",
                    "carModelOfficialSpeedupTime": "",
                    "carModelReleaseTime": "2013.05",
                    "carModelSize": "5095*1875*1485",
                    "carModelSpecId": "16147",
                    "carModelSpecUrl": "https://www.autohome.com.cn/spec/16147/",
                    "carModelWholeWarranty": "四年或10万公里",
                    "carModelYear": "2013款",
                    "carSeriesId": "2771",
                    "carSeriesLevelId": "5",
                    "carSeriesLevelName": "中大型车",
                    "carSeriesMainImgUrl": "https://car3.autoimg.cn/cardfs/product/g27/M07/94/4F/380x285_0_q87_autohomecar__ChsEnV6MPieAbbAgAAiIIauI0dE436.jpg",
                    "carSeriesMaxPrice": "31.78万",
                    "carSeriesMinPrice": "25.28万",
                    "carSeriesMsrp": "25.28-31.78万",
                    "carSeriesMsrpUrl": "https://www.autohome.com.cn/2771/price.html#pvareaid=101446",
                    "carSeriesName": "红旗H7",
                    "carSeriesUrl": "https://www.autohome.com.cn/2771/#levelsource=000000000_0&pvareaid=101594"
                }
            
            https://www.autohome.com.cn/spec/46144/
            {
                "carBrandId": "36",
                "carBrandLogoUrl": "https://car3.autoimg.cn/cardfs/series/g26/M00/AF/E7/100x100_f40_autohomecar__wKgHHVs9u6mAaY6mAAA2M840O5c440.png",
                "carBrandName": "奔驰",
                "carEnergyType": "汽油",
                "carMerchantName": "北京奔驰",
                "carMerchantUrl": "https://car.autohome.com.cn/price/brand-36-152.html#pvareaid=2042363",
                "carModelActualFuelConsumption": "",
                "carModelActualTestBrakeDistance": "39.01",
                "carModelActualTestEnduranceMileage": "",
                "carModelActualTestQuickCharge": "",
                "carModelActualTestSlowCharge": "",
                "carModelActualTestSpeedupTime": "9.01",
                "carModelBodyStructure": "5门5座SUV",
                "carModelDataSift2": "国VI",
                "carModelDataSift3": "1.3T",
                "carModelDataSift4": "7挡双离合",
                "carModelDriveType": "前置前驱",
                "carModelEngine": "1.3T 163马力 L4",
                "carModelEnvStandard": "国VI",
                "carModelGearBox": "7挡双离合",
                "carModelGroupName": "1.3升 涡轮增压 163马力 国VI",
                "carModelHorsePowerElectric": "",
                "carModelMaxPower": "120",
                "carModelMaxSpeed": "207",
                "carModelMaxTorque": "250",
                "carModelMiitCompositeFuelConsumption": "6.1",
                "carModelMiitEnduranceMileagePureElectric": "",
                "carModelMsrp": "30.38万",
                "carModelName": "2020款 GLA 200",
                "carModelOfficialSpeedupTime": "9",
                "carModelQuickCharge": "",
                "carModelQuickChargePercent": "",
                "carModelReleaseTime": "2020.07",
                "carModelSize": "4417*1834*1610",
                "carModelSlowCharge": "",
                "carModelSpecId": "46144",
                "carModelSpecUrl": "https://www.autohome.com.cn/spec/46144/#pvareaid=3454492",
                "carModelWholeWarranty": "三年不限公里",
                "carModelYear": "2020款",
                "carSeriesId": "3248",
                "carSeriesLevelId": "17",
                "carSeriesLevelName": "紧凑型SUV",
                "carSeriesMainImgUrl": "https://car3.autoimg.cn/cardfs/product/g27/M04/4F/39/380x285_0_q87_autohomecar__ChwFkV8eQZSAPD0IAAz4_sk-g8M069.jpg",
                "carSeriesMaxPrice": "30.38万",
                "carSeriesMinPrice": "30.38万",
                "carSeriesMsrp": "30.38-30.38万",
                "carSeriesMsrpUrl": "https://www.autohome.com.cn/3248/price.html#pvareaid=101446",
                "carSeriesName": "奔驰GLA",
                "carSeriesUrl": "https://www.autohome.com.cn/3248/#levelsource=000000000_0&pvareaid=101594"
            }

        纯电动
            https://www.autohome.com.cn/spec/42875/
                {
                    "carBrandId": "33",
                    "carBrandLogoUrl": "https://car2.autoimg.cn/cardfs/series/g26/M0B/AE/B3/100x100_f40_autohomecar__wKgHEVs9u5WAV441AAAKdxZGE4U148.png",
                    "carBrandName": "奥迪",
                    "carEnergyType": "纯电动",
                    "carMerchantName": "一汽-大众奥迪",
                    "carMerchantUrl": "https://car.autohome.com.cn/price/brand-33-9.html#pvareaid=2042363",
                    "carModelActualTestBrakeDistance": "",
                    "carModelActualTestEnduranceMileage": "",
                    "carModelActualTestQuickCharge": "",
                    "carModelActualTestSlowCharge": "",
                    "carModelActualTestSpeedupTime": "",
                    "carModelBodyStructure": "5门5座SUV",
                    "carModelDataSift2": "100KW",
                    "carModelDataSift3": "265公里",
                    "carModelDataSift4": "单速",
                    "carModelDriveType": "前置前驱",
                    "carModelGearBox": "电动车单速变速箱",
                    "carModelGroupName": "电动 136马力",
                    "carModelHorsePowerElectric": "136",
                    "carModelMaxPower": "100",
                    "carModelMaxSpeed": "150",
                    "carModelMaxTorque": "290",
                    "carModelMiitEnduranceMileagePureElectric": "265",
                    "carModelMsrp": "22.68万",
                    "carModelName": "2019款 Q2L e-tron 纯电智酷型",
                    "carModelOfficialSpeedupTime": "",
                    "carModelQuickCharge": "0.6",
                    "carModelQuickChargePercent": "80",
                    "carModelReleaseTime": "2019.11",
                    "carModelSize": "4237*1785*1548",
                    "carModelSlowCharge": "17",
                    "carModelSpecId": "42875",
                    "carModelSpecUrl": "https://www.autohome.com.cn/spec/42875/#pvareaid=3454492",
                    "carModelWholeWarranty": "三年或10万公里",
                    "carModelYear": "2019款",
                    "carSeriesId": "5240",
                    "carSeriesLevelId": "16",
                    "carSeriesLevelName": "小型SUV",
                    "carSeriesMainImgUrl": "https://car2.autoimg.cn/cardfs/product/g26/M08/5E/E9/380x285_0_q87_autohomecar__ChsEnFz-PK6AKWR5AAb_0TkX5cE445.jpg",
                    "carSeriesMaxPrice": "23.73万",
                    "carSeriesMinPrice": "22.68万",
                    "carSeriesMsrp": "22.68-23.73万",
                    "carSeriesMsrpUrl": "https://www.autohome.com.cn/5240/price.html#pvareaid=101446",
                    "carSeriesName": "奥迪Q2L e-tron",
                    "carSeriesUrl": "https://www.autohome.com.cn/5240/#levelsource=000000000_0&pvareaid=101594"
                }
        
        油电混合
            https://car.autohome.com.cn/config/spec/35507.html
                {
                    "carBrandId": "52",
                    "carBrandLogoUrl": "https://car2.autoimg.cn/cardfs/series/g29/M02/B0/BE/100x100_f40_autohomecar__ChcCSFs91WqAGpOHAABVaN6-df4803.png",
                    "carBrandName": "雷克萨斯",
                    "carEnergyType": "油电混合",
                    "carMerchantName": "雷克萨斯",
                    "carMerchantUrl": "https://car.autohome.com.cn/price/brand-52-65.html#pvareaid=2042363",
                    "carModelActualFuelConsumption": "",
                    "carModelActualTestBrakeDistance": "",
                    "carModelActualTestEnduranceMileage": "",
                    "carModelActualTestQuickCharge": "",
                    "carModelActualTestSlowCharge": "",
                    "carModelActualTestSpeedupTime": "",
                    "carModelBodyStructure": "5门5座两厢车",
                    "carModelDataSift2": "",
                    "carModelDataSift3": "",
                    "carModelDataSift4": "",
                    "carModelDriveType": "前驱",
                    "carModelEngine": "1.8L 99马力 L4",
                    "carModelEnvStandard": "国IV(国V)",
                    "carModelGearBox": "E-CVT无级变速",
                    "carModelGroupName": "1.8升 99马力",
                    "carModelHorsePowerElectric": "82",
                    "carModelMaxPower": "100",
                    "carModelMaxSpeed": "",
                    "carModelMaxTorque": "",
                    "carModelMiitCompositeFuelConsumption": "4.6",
                    "carModelMiitEnduranceMileagePureElectric": "",
                    "carModelMsrp": "26.70万",
                    "carModelName": "2018款 CT200h 多彩生活特别限量版",
                    "carModelOfficialSpeedupTime": "",
                    "carModelQuickCharge": "",
                    "carModelQuickChargePercent": "",
                    "carModelReleaseTime": "2018.08",
                    "carModelSize": "4360*1765*1455",
                    "carModelSlowCharge": "",
                    "carModelSpecId": "35507",
                    "carModelSpecUrl": "https://www.autohome.com.cn/spec/35507/",
                    "carModelWholeWarranty": "六年或15万公里",
                    "carModelYear": "2018款",
                    "carSeriesId": "2063",
                    "carSeriesLevelId": "3",
                    "carSeriesLevelName": "紧凑型车",
                    "carSeriesMainImgUrl": "https://car2.autoimg.cn/cardfs/product/g29/M09/FB/2F/380x285_0_q87_autohomecar__ChsEfl9GUImAT_62AAnvWT7-yrA464.jpg",
                    "carSeriesMaxPrice": "28.20万",
                    "carSeriesMinPrice": "21.50万",
                    "carSeriesMsrp": "21.50-28.20万",
                    "carSeriesMsrpUrl": "https://www.autohome.com.cn/2063/price.html#pvareaid=101446",
                    "carSeriesName": "雷克萨斯CT",
                    "carSeriesUrl": "https://www.autohome.com.cn/2063/#levelsource=000000000_0&pvareaid=101594"
                }
        """

        carAllKeyList = [
            "carBrandName",
            "carBrandId",
            "carBrandLogoUrl",
            "carMerchantName",
            "carMerchantUrl",
            "carSeriesId",
            "carSeriesName",
            "carSeriesUrl",
            "carSeriesMsrp",
            "carSeriesMsrpUrl",
            "carSeriesMainImgUrl",
            "carSeriesMinPrice",
            "carSeriesMaxPrice",
            "carSeriesLevelName",
            "carSeriesLevelId",
            "carModelName",
            "carModelSpecUrl",
            "carModelSpecId",
            "carModelMsrp",
            "carModelYear",
            "carModelGearBox",
            "carModelDriveType",
            "carModelBodyStructure",
            "carModelEngine",
            "carModelGroupName",
            "carModelDataSift2",
            "carModelDataSift3",
            "carModelDataSift4",
            "carEnergyType",
            "carModelEnvStandard",
            "carModelReleaseTime",
            "carModelMaxPower",
            "carModelMaxTorque",
            "carModelSize",
            "carModelMaxSpeed",
            "carModelOfficialSpeedupTime",
            "carModelActualTestSpeedupTime",
            "carModelActualTestBrakeDistance",
            "carModelMiitCompositeFuelConsumption",
            "carModelActualFuelConsumption",
            "carModelMiitEnduranceMileagePureElectric",
            "carModelQuickCharge",
            "carModelSlowCharge",
            "carModelQuickChargePercent",
            "carModelHorsePowerElectric",
            "carModelActualTestEnduranceMileage",
            "carModelActualTestQuickCharge",
            "carModelActualTestSlowCharge",
            "carModelWholeWarranty",
        ]

        for eachCarKey in carAllKeyList:
            if eachCarKey not in carModelDict:
                print("found miss key: %s" % eachCarKey)
                carModelDict[eachCarKey] = ""

        carModelSpecUrl = carModelDict["carModelSpecUrl"]
        self.send_message(self.project_name, carModelDict, url=carModelSpecUrl)

    def on_message(self, project, msg):
        print("on_message: msg=%s" % msg)
        return msg

