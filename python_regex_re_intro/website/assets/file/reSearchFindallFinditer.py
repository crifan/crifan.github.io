# Function: Demo re.search re.findall re.finditer
# Author: Crifan Li
# Update: 20201212

import re

singleLineMdStr = "* [科学上网](https://book.crifan.com/books/scientific_network_summary/website)"

foundBook = re.search("https?://book\.crifan\.com/books/(?P<bookName>\w+)/website", singleLineMdStr)
print("foundBook=%s" % foundBook)
# foundBook=<re.Match object; span=(9, 73), match='https://book.crifan.com/books/scientific_network_>
if foundBook:
  bookName = foundBook.group("bookName")
  print("bookName=%s" % bookName)
  # bookName=scientific_network_summary

multipleLineDdStr = """
* 推荐工具
  * [科学上网](https://book.crifan.com/books/scientific_network_summary/website)
  * 编辑器和IDE
    * [总结](https://book.crifan.com/books/editor_ide_summary/website/)
    * 好用工具
      * [VSCode](http://book.crifan.com/books/best_editor_vscode/website)
"""

allBookUrlList = re.findall("https?://book\.crifan\.com/books/\w+/website", multipleLineDdStr)
print("allBookUrlList=%s" % allBookUrlList)
# allBookUrlList=['https://book.crifan.com/books/scientific_network_summary/website', 'https://book.crifan.com/books/editor_ide_summary/website', 'http://book.crifan.com/books/best_editor_vscode/website']

allBookNameList = re.findall("https?://book\.crifan\.com/books/(?P<bookName>\w+)/website", multipleLineDdStr)
print("allBookNameList=%s" % allBookNameList)
# allBookNameList=['scientific_network_summary', 'editor_ide_summary', 'best_editor_vscode']

allBookUrlMatchObjIterator = re.finditer("https?://book\.crifan\.com/books/\w+/website", multipleLineDdStr)
print("allBookUrlMatchObjIterator=%s" % allBookUrlMatchObjIterator)
# allBookUrlMatchObjIterator=<callable_iterator object at 0x11063f160>
allBookUrlMatchObjList = list(allBookUrlMatchObjIterator)
print("allBookUrlMatchObjList=%s" % allBookUrlMatchObjList)
# allBookUrlMatchObjList=[<re.Match object; span=(19, 83), match='https://book.crifan.com/books/scientific_network_>, <re.Match object; span=(108, 164), match='https://book.crifan.com/books/editor_ide_summary/>, <re.Match object; span=(195, 250), match='http://book.crifan.com/books/best_editor_vscode/w>]
for curIdx, eachMatchObj in enumerate(allBookUrlMatchObjList):
  singleMatchWholeStr = eachMatchObj.group(0)
  print("[%d] singleMatchWholeStr=%s" % (curIdx, singleMatchWholeStr))
# [0] singleMatchWholeStr=https://book.crifan.com/books/scientific_network_summary/website
# [1] singleMatchWholeStr=https://book.crifan.com/books/editor_ide_summary/website
# [2] singleMatchWholeStr=http://book.crifan.com/books/best_editor_vscode/website

allBookNameMatchObjIterator = re.finditer("https?://book\.crifan\.com/books/(?P<bookName>\w+)/website", multipleLineDdStr)
print("allBookNameMatchObjIterator=%s" % allBookNameMatchObjIterator)
# allBookNameMatchObjIterator=<callable_iterator object at 0x10e9a9fd0>
allBookNameMatchObjList = list(allBookNameMatchObjIterator)
print("allBookNameMatchObjList=%s" % allBookNameMatchObjList)
# allBookNameMatchObjList=[<re.Match object; span=(19, 83), match='https://book.crifan.com/books/scientific_network_>, <re.Match object; span=(108, 164), match='https://book.crifan.com/books/editor_ide_summary/>, <re.Match object; span=(195, 250), match='http://book.crifan.com/books/best_editor_vscode/w>]
for curIdx, eachMatchObj in enumerate(allBookNameMatchObjList):
  singleMatchWholeStr = eachMatchObj.group(0)
  singleMatchBookName = eachMatchObj.group("bookName")
  print("[%d] singleMatchWholeStr=%s, singleMatchBookName=%s" % (curIdx, singleMatchWholeStr, singleMatchBookName))
# [0] singleMatchWholeStr=https://book.crifan.com/books/scientific_network_summary/website, singleMatchBookName=scientific_network_summary
# [1] singleMatchWholeStr=https://book.crifan.com/books/editor_ide_summary/website, singleMatchBookName=editor_ide_summary
# [2] singleMatchWholeStr=http://book.crifan.com/books/best_editor_vscode/website, singleMatchBookName=best_editor_vscode
