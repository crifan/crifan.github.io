# -*- coding: utf-8 -*-
# Quick Explanation Python 3 Basic Syntax For Programmers
# 一图搞懂Python3基本语法

import os

def main():
    print('Hello World!') # 字符串用单引号

    print("This is CrifanLi\'的问候 \U0001f604") # 字符串用双引号，带反斜杠转义，带unicode字符：😄

    foo(5, 20) # 也可以写成：foo(5)

    print("=" * 10)
    print("这将直接运行 " + os.getcwd())

    counter = 0
    counter += 1

    food = ["苹果", "桔子", "🍌", "🍐"]
    for curFood in food:
        print("我喜欢吃水果："+curFood)

    print("数到5")
    for i in range(5):
        print(i)

def foo(param1, secondParam=20):
    result = param1 + secondParam
    print("%s + %s 等于 %s" % (param1, secondParam, result))
    if result < 50:
        print("第一种情况")
    elif (result >= 50) and (param1 == 42) or (secondParam == 24):
        print("情况2")
    else:
        print("其他情况")

    return result # 这个是单行注释
    """
    这个是
        多行注释
    """

if __name__ == "__main__":
    main()