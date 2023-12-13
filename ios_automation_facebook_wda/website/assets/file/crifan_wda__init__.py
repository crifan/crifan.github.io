#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Updated: 20200609 17:01
# Editor: Crifan Li

from __future__ import print_function, unicode_literals

import base64
import copy
import functools
import io
import json
import os
import re
import threading
import time
from collections import defaultdict, namedtuple

import requests
import retry
import six
from six.moves import urllib
try:
    from functools import cached_property # Python3.8+
except ImportError:
    from cached_property import cached_property

from . import xcui_element_types

import logging
from enum import Enum

urlparse = urllib.parse.urlparse
_urljoin = urllib.parse.urljoin

if six.PY3:
    from functools import reduce

DEBUG = False
# to change to logging -> later can use colorful logging
print = logging.debug

HTTP_TIMEOUT = 60.0  # unit second

# RETRY_INTERVAL = 0.01
RETRY_INTERVAL = 0.1

LANDSCAPE = 'LANDSCAPE'
PORTRAIT = 'PORTRAIT'
LANDSCAPE_RIGHT = 'UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT'
PORTRAIT_UPSIDEDOWN = 'UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN'

alert_callback = None

JSONDecodeError = json.decoder.JSONDecodeError if hasattr(
    json.decoder, "JSONDecodeError") else ValueError

################################################################################
# Definition
################################################################################

# https://developer.apple.com/documentation/uikit/uidevice/1620042-batterylevel?language=objc
class BatteryState(Enum):
    Unknown = 0
    Unplugged = 1
    Charging = 2
    Full = 3

# https://developer.apple.com/documentation/xctest/xctimagequality?language=objc
class ScreenshotQuality(Enum):
    Original = 0 # lossless PNG image
    Medium = 1 # high quality lossy JPEG image
    Low = 2 # highly compressed lossy JPEG image

# https://developer.apple.com/documentation/xctest/xcuiapplicationstate?language=objc
class ApplicationState(Enum):
    Unknown = 0
    NotRunning = 1
    RunningBackgroundSuspended = 2
    RunningBackground = 3
    RunningForeground = 4


class WDAError(Exception):
    """ base wda error """


class WDARequestError(WDAError):
    def __init__(self, status, value):
        self.status = status
        self.value = value

    def __str__(self):
        return 'WDARequestError(status=%d, value=%s)' % (self.status,
                                                         self.value)


class WDAEmptyResponseError(WDAError):
    """ response body is empty """


class WDAElementNotFoundError(WDAError):
    """ element not found """


class WDAElementNotDisappearError(WDAError):
    """ element not disappera """


################################################################################
# Utils Functions
################################################################################

def convert(dictionary):
    """
    Convert dict to namedtuple
    """
    return namedtuple('GenericDict', list(dictionary.keys()))(**dictionary)


def urljoin(*urls):
    """
    The default urlparse.urljoin behavior look strange
    Standard urlparse.urljoin('http://a.com/foo', '/bar')
    Expect: http://a.com/foo/bar
    Actually: http://a.com/bar

    This function fix that.
    """
    return reduce(_urljoin, [u.strip('/') + '/' for u in urls if u.strip('/')],
                  '').rstrip('/')


def roundint(i):
    return int(round(i, 0))


def namedlock(name):
    """
    Returns:
        threading.Lock
    """
    if not hasattr(namedlock, 'locks'):
        namedlock.locks = defaultdict(threading.Lock)
    return namedlock.locks[name]


def httpdo(url, method="GET", data=None):
    """
    thread safe http request
    """
    p = urlparse(url)
    with namedlock(p.scheme + "://" + p.netloc):
        return _unsafe_httpdo(url, method, data)


def _unsafe_httpdo(url, method='GET', data=None):
    """
    Do HTTP Request
    """
    start = time.time()
    if DEBUG:
        body = json.dumps(data) if data else ''
        print("Shell: curl -X {method} -d '{body}' '{url}'".format(
            method=method.upper(), body=body or '', url=url))

    try:
        response = requests.request(method,
                                    url,
                                    json=data,
                                    timeout=HTTP_TIMEOUT)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout) as e:
        raise

    if DEBUG:
        ms = (time.time() - start) * 1000
        print('Return ({:.0f}ms): {}'.format(ms, response.text))

    try:
        retjson = response.json()
        retjson['status'] = retjson.get('status', 0)
        r = convert(retjson)
        if r.status != 0:
            raise WDARequestError(r.status, r.value)
        if isinstance(r.value, dict) and r.value.get("error"):
            raise WDARequestError(100, r.value['error']) # status:100 for new WebDriverAgent error
        return r
    except JSONDecodeError:
        if response.text == "":
            raise WDAEmptyResponseError(method, url, data)
        raise WDAError(method, url, response.text)


################################################################################
# Main
################################################################################


class HTTPClient(object):
    def __init__(self, address, alert_callback=None):
        """
        Args:
            address (string): url address eg: http://localhost:8100
            alert_callback (func): function to call when alert popup
        """
        self.address = address
        self.alert_callback = alert_callback

    def new_client(self, path):
        return HTTPClient(
            self.address.rstrip('/') + '/' + path.lstrip('/'),
            self.alert_callback)

    def fetch(self, method, url, data=None):
        return self._fetch_no_alert(method, url, data)
        # return httpdo(urljoin(self.address, url), method, data)

    def _fetch_no_alert(self, method, url, data=None, depth=0):
        target_url = urljoin(self.address, url)
        try:
            return httpdo(target_url, method, data)
        except WDARequestError as err:
            if depth >= 10:
                raise
            if err.status != 26:  # alert status code
                raise
            if not callable(self.alert_callback):
                raise
            self.alert_callback()
            return self._fetch_no_alert(method, url, data, depth=depth + 1)

    def __getattr__(self, key):
        """ Handle GET,POST,DELETE, etc ... """
        return functools.partial(self.fetch, key)


class Rect(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __str__(self):
        return 'Rect(x={x}, y={y}, width={w}, height={h})'.format(
            x=self.x, y=self.y, w=self.width, h=self.height)

    def __repr__(self):
        return str(self)

    # @property
    @cached_property
    def center(self):
        if DEBUG:
            print("calc center position")
        return namedtuple('Point', ['x', 'y'])(self.x + self.width / 2,
                                               self.y + self.height / 2)

    @property
    def origin(self):
        return namedtuple('Point', ['x', 'y'])(self.x, self.y)

    @property
    def left(self):
        return self.x

    @property
    def top(self):
        return self.y

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def x0(self):
        return self.x

    @property
    def y0(self):
        return self.y

    @property
    def x1(self):
        return self.x + self.width

    @property
    def y1(self):
        return self.y + self.height

    @property
    def centerX(self):
        return self.center[0]
        # return self.center["x"]

    @property
    def centerY(self):
        return self.center[1]
        # return self.center["y"]

    @property
    def isZero(self):
        isXZero = self.x == 0
        isYZero = self.y == 0
        isWidthZero = self.width == 0
        isHeightZero = self.height == 0
        isAllZero = isXZero and isYZero and isWidthZero and isHeightZero
        return isAllZero


class Client(object):
    def __init__(self, url=None, _session_id=None):
        """
        Args:
            target (string): the device url
        
        If target is empty, device url will set to env-var "DEVICE_URL" if defined else set to "http://localhost:8100"
        """
        if not url:
            url = os.environ.get('DEVICE_URL', 'http://localhost:8100')
        assert re.match(r"^https?://", url), "Invalid URL: %r" % url

        self.http = HTTPClient(url)
        
        # Session variable
        self.__session_id = _session_id
        self.__timeout = 30.0
        self.__target = None

    def wait_ready(self, timeout=120):
        """
        wait until WDA back to normal

        Returns:
            bool (if wda works)
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self.status()
                return True
            except:
                time.sleep(2)
        return False

    @retry.retry(exceptions=WDAEmptyResponseError, tries=3, delay=2)
    def status(self):
        res = self.http.get('status')
        sid = res.sessionId
        res.value['sessionId'] = sid
        return res.value

    def home(self):
        """Press home button"""
        return self.http.post('/wda/homescreen')

    def healthcheck(self):
        """Hit healthcheck"""
        return self.http.get('/wda/healthcheck')

    def locked(self):
        """ returns locked status, true or false """
        return self.http.get("/wda/locked").value

    def lock(self):
        return self.http.post('/wda/lock')

    def unlock(self):
        """ unlock screen, double press home """
        return self.http.post('/wda/unlock')

    def app_current(self):
        """
        Returns:
            dict, eg:
            {
                "running" : true,
                "state" : 4,
                "generation" : 0,
                "processArguments" : {
                    "env" : {},
                    "args" : []
                },
                "title" : "",
                "bundleId" : "com.tencent.xin",
                "label" : "微信",
                "path" : "",
                "name" : "",
                "pid" : 1357
            }
        """
        return self.http.get("/wda/activeAppInfo").value

    def source(self, format='xml', accessible=False):
        """
        Args:
            format (str): only 'xml' and 'json' source types are supported
            accessible (bool): when set to true, format is always 'json'
        """
        if accessible:
            return self.http.get('/wda/accessibleSource').value
        return self.http.get('source?format=' + format).value

    def screenshot(self, png_filename=None, format='pillow'):
        """
        Screenshot with PNG format

        Args:
            png_filename(string): optional, save file name
            format(string): return format, "raw" or "pillow" (default)
        
        Returns:
            PIL.Image or raw png data
        
        Raises:
            WDARequestError
        """
        value = self.http.get('screenshot').value
        raw_value = base64.b64decode(value)
        png_header = b"\x89PNG\r\n\x1a\n"
        if not raw_value.startswith(png_header) and png_filename:
            raise WDARequestError(-1, "screenshot png format error")

        if png_filename:
            with open(png_filename, 'wb') as f:
                f.write(raw_value)

        if format == 'raw':
            return raw_value
        elif format == 'pillow':
            from PIL import Image
            buff = io.BytesIO(raw_value)
            return Image.open(buff)
        else:
            raise ValueError("unknown format")

    def session(self,
                bundle_id=None,
                arguments=None,
                environment=None,
                alert_action=None):
        """
        Args:
            - bundle_id (str): the app bundle id
            - arguments (list): ['-u', 'https://www.google.com/ncr']
            - enviroment (dict): {"KEY": "VAL"}
            - alert_action (str): "accept" or "dismiss"

        WDA Return json like

        {
            "value": {
                "sessionId": "69E6FDBA-8D59-4349-B7DE-A9CA41A97814",
                "capabilities": {
                    "device": "iphone",
                    "browserName": "部落冲突",
                    "sdkVersion": "9.3.2",
                    "CFBundleIdentifier": "com.supercell.magic"
                }
            },
            "sessionId": "69E6FDBA-8D59-4349-B7DE-A9CA41A97814",
            "status": 0
        }

        To create a new session, send json data like

        {
            "desiredCapabilities": {
                "bundleId": "your-bundle-id",
                "app": "your-app-path"
                "shouldUseCompactResponses": (bool),
                "shouldUseTestManagerForVisibilityDetection": (bool),
                "maxTypingFrequency": (integer),
                "arguments": (list(str)),
                "environment": (dict: str->str)
            },
        }
        """
        if bundle_id is None:
            return self

        if arguments and type(arguments) is not list:
            raise TypeError('arguments must be a list')

        if environment and type(environment) is not dict:
            raise TypeError('environment must be a dict')

        capabilities = {
            'bundleId': bundle_id,
            'arguments': arguments,
            'environment': environment,
            'shouldWaitForQuiescence': False,
            # In the latest appium/WebDriverAgent, set shouldWaitForQuiescence to True will stuck
            # 'useJSONSource': True,
            # 'simpleIsVisibleCheck': True,
            # 'shouldUseTestManagerForVisibilityDetection': True,
        }
        # Remove empty value to prevent WDARequestError
        for k in list(capabilities.keys()):
            if capabilities[k] is None:
                capabilities.pop(k)

        if alert_action:
            assert alert_action in ["accept", "dismiss"]
            capabilities["defaultAlertAction"] = alert_action

        data = {
            'desiredCapabilities': capabilities,  # For old WDA
            "capabilities": {
                "alwaysMatch": capabilities,  # For recent WDA 2019/08/28
            }
        }
        if DEBUG:
            print("data=%s" % data)
        try:
            res = self.http.post('session', data)
            # if DEBUG:
            #     # print("res=%s" % res)
            #     # respJson = res.json()
            #     # print("respJson=%s" % respJson)
            #     respDict = dict(res)
            #     print("respDict=%s" % respDict)
        except WDAEmptyResponseError:
            """ when there is alert, might be got empty response
            use /wda/apps/state may still get sessionId
            """
            res = self.session().app_state(bundle_id)
            if res.value != 4:
                raise
        return Client(self.http.address, _session_id=res.sessionId)

    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
    ######  Session methods and properties ######
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
    def __str__(self):
        # return 'wda.Client (sessionId=%s)' % self._sid
        return 'wda.Client (sessionId=%s)' % self.__session_id

    def __enter__(self):
        """
        Usage example:
            with c.session("com.example.app") as app:
                # do something
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def id(self):
        return self._session_id

    @property
    def _session_id(self) -> str:
        if self.__session_id:
            return self.__session_id
        return self.status()['sessionId']
        
    @property
    def _session_http(self) -> HTTPClient:
        return self.http.new_client("session/"+self._session_id)
    
    @cached_property
    def scale(self):
        """
        UIKit scale factor
        
        Refs:
            https://developer.apple.com/library/archive/documentation/DeviceInformation/Reference/iOSDeviceCompatibility/Displays/Displays.html
        There is another way to get scale
            self.http.get("/wda/screen").value returns {"statusBarSize": {'width': 320, 'height': 20}, 'scale': 2}
        """
        v = max(self.screenshot().size) / max(self.window_size())
        if DEBUG:
            print("v=%s" % v)
        return round(v)
    
    @cached_property
    def bundle_id(self):
        """ the session matched bundle id """
        v = self._session_http.get("/").value
        return v['capabilities'].get('CFBundleIdentifier')
    
    def implicitly_wait(self, seconds):
        """
        set default element search timeout
        """
        assert isinstance(seconds, (int, float))
        self.__timeout = seconds
    
    def battery_info(self):
        """
        Returns dict:
            eg: {"level": 1, "state": 2}
            level: 0 ~ 1.0, battery electricity percent
            state: unknown=0, unplugged=1, charging=2, full=3
                https://developer.apple.com/documentation/uikit/uidevice/batterystate
        """
        return self._session_http.get("/wda/batteryInfo").value

    def matchTouchID(self):
        postResp = self._session_http.post("/wda/touch_id", {
            "match": 1,
        })
        respValue = postResp.value
        if DEBUG:
            print("/wda/touch_id: respValue=%s" % respValue)
        return respValue

    def device_info(self):
        """
        Returns dict:
            eg: {'currentLocale': 'zh_CN', 'timeZone': 'Asia/Shanghai'}
        """
        return self._session_http.get("/wda/device/info").value

    def screen_info(self):
        """get screen info
            https://developer.apple.com/library/archive/documentation/DeviceInformation/Reference/iOSDeviceCompatibility/Displays/Displays.html

        Returns dict:
            eg: 
                {'statusBarSize': {'width': 375, 'height': 20}, 'scale': 2}
                -> updated wda code, can return more info:
                {'statusBarSize': {'width': 375, 'height': 20}, 'nativeScale': 2.88, 'nativeBounds': {'y': 0, 'x': 0, 'width': 921, 'height': 1382}, 'bounds': {'y': 0, 'x': 0, 'width': 320, 'height': 480}, 'scale': 2}
        """
        if DEBUG:
            print("self._session_http=%s" % self._session_http)

        return self._session_http.get("/wda/screen").value
        # return self.http.get("/wda/screen").value

    def window_info(self):
        """get window size info

        Returns dict:
            eg: {'width': 375, 'height': 667}
        """
        return self._session_http.get("/window/size").value
        # return self.http.get("/window/size").value

    def get_settings(self):
        resp = self._session_http.get("/appium/settings")
        respSettings = resp.value
        if DEBUG:
            # print("resp=%s" % resp) #  TypeError not all arguments converted during string formatting
            print("respSettings=%s" % respSettings)
        return respSettings

    def set_settings(self, newSettings):
        postResp = self._session_http.post("/appium/settings", {
            "settings": newSettings,
        })
        respNewSettings = postResp.value
        if DEBUG:
            print("respNewSettings=%s" % respNewSettings)
        return respNewSettings

    def setSnapshotTimeout(self, newSnapshotTimeout):
        """set new snapshotTimeout value for current session /appium/settings"""
        newSettings = {
            "snapshotTimeout": newSnapshotTimeout
        }
        return self.set_settings(newSettings)
    def set_clipboard(self, content, content_type="plaintext"):
        """ set clipboard """
        self._session_http.post(
            "/wda/setPasteboard", {
                "content": base64.b64encode(content.encode()).decode(),
                "contentType": content_type
            })
    
    def set_alert_callback(self, callback):
        """
        Args:
            callback (func): called when alert popup
        
        Example of callback:

            def callback(session):
                session.alert.accept()
        """
        if callable(callback):
            self.http.alert_callback = functools.partial(callback, self)
        else:
            self.http.alert_callback = None

    #Not working
    #def get_clipboard(self):
    #   self.http.post("/wda/getPasteboard").value

    # Not working
    #def siri_activate(self, text):
    #    self.http.post("/wda/siri/activate", {"text": text})

    def app_launch(self,
                   bundle_id,
                   arguments=[],
                   environment={},
                   wait_for_quiescence=False):
        """
        Args:
            - bundle_id (str): the app bundle id
            - arguments (list): ['-u', 'https://www.google.com/ncr']
            - enviroment (dict): {"KEY": "VAL"}
            - wait_for_quiescence (bool): default False
        """
        assert isinstance(arguments, (tuple, list))
        assert isinstance(environment, dict)

        return self._session_http.post(
            "/wda/apps/launch", {
                "bundleId": bundle_id,
                "arguments": arguments,
                "environment": environment,
                "shouldWaitForQuiescence": wait_for_quiescence,
            })

    def app_activate(self, bundle_id):
        return self._session_http.post("/wda/apps/launch", {
            "bundleId": bundle_id,
        })

    def app_terminate(self, bundle_id):
        return self._session_http.post("/wda/apps/terminate", {
            "bundleId": bundle_id,
        })

    def app_state(self, bundle_id):
        """
        Returns example:
            {
                "value": 4,
                "sessionId": "0363BDC5-4335-47ED-A54E-F7CCB65C6A65"
            }
        
            value: enum ApplicationState
        """
        return self._session_http.post("/wda/apps/state", {
            "bundleId": bundle_id,
        })

    def app_list(self):
        """
        Not working very well, only show springboard

        Returns:
            list of app
        
        Return example:
            [{'pid': 52, 'bundleId': 'com.apple.springboard'}]
        """
        return self._session_http.get("/wda/apps/list").value

    def open_url(self, url):
        """
        TODO: Never successed using before. Looks like use Siri to search.
        https://github.com/facebook/WebDriverAgent/blob/master/WebDriverAgentLib/Commands/FBSessionCommands.m#L43
        Args:
            url (str): url
        
        Raises:
            WDARequestError
        """
        return self._session_http.post('url', {'url': url})

    def deactivate(self, duration):
        """Put app into background and than put it back
        Args:
            - duration (float): deactivate time, seconds
        """
        return self._session_http.post('/wda/deactivateApp', dict(duration=duration))

    def tap(self, x, y):
        return self._session_http.post('/wda/tap/0', dict(x=x, y=y))

    def _percent2pos(self, x, y, window_size=None):
        if DEBUG:
            print("x=%s, y=%s, window_size=%s" % (x, y, window_size))

        if any(isinstance(v, float) for v in [x, y]):
            w, h = window_size or self.window_size()
            if DEBUG:
                print("type(w)=%s" % type(w))
                print("type(h)=%s" % type(h))
                print("w=%s, h=%s" % (w, h))

            # x = int(x * w) if isinstance(x, float) else x
            # y = int(y * h) if isinstance(y, float) else y
            if isinstance(x, float):
                if (x > 0.0) and (x <= 1.0):
                    convertedX = x * w
                    xInt = int(convertedX)
                else:
                    # consider as real float position value
                    xInt = int(x)
                x = xInt

            if isinstance(y, float):
                if (y > 0.0) and (y <= 1.0):
                    convertedY = y * h
                    yInt = int(convertedY)
                else:
                    # consider as real float position value
                    yInt = int(y)
                y = yInt

            if DEBUG:
                print("type(x)=%s" % type(x))
                print("type(y)=%s" % type(y))
                print("x=%s, y=%s" % (x, y))

            assert w >= x >= 0
            assert h >= y >= 0
        return (x, y)

    def click(self, x, y):
        """
        x, y can be float(percent) or int
        """
        x, y = self._percent2pos(x, y)
        return self.tap(x, y)

    def double_tap(self, x, y):
        x, y = self._percent2pos(x, y)
        return self._session_http.post('/wda/doubleTap', dict(x=x, y=y))

    def tap_hold(self, x, y, duration=1.0):
        """
        Tap and hold for a moment

        Args:
            - x, y(int, float): float(percent) or int(absolute coordicate)
            - duration(float): seconds of hold time

        [[FBRoute POST:@"/wda/touchAndHold"] respondWithTarget:self action:@selector(handleTouchAndHoldCoordinate:)],
        """
        x, y = self._percent2pos(x, y)
        data = {'x': x, 'y': y, 'duration': duration}
        return self._session_http.post('/wda/touchAndHold', data=data)

    def swipe(self, x1, y1, x2, y2, duration=0):
        """
        Args:
            x1, y1, x2, y2 (int, float): float(percent), int(coordicate)
            duration (float): start coordinate press duration (seconds)

        [[FBRoute POST:@"/wda/dragfromtoforduration"] respondWithTarget:self action:@selector(handleDragCoordinate:)],
        """
        if any(isinstance(v, float) for v in [x1, y1, x2, y2]):
            size = self.window_size()
            x1, y1 = self._percent2pos(x1, y1, size)
            x2, y2 = self._percent2pos(x2, y2, size)

        data = dict(fromX=x1, fromY=y1, toX=x2, toY=y2, duration=duration)
        return self._session_http.post('/wda/dragfromtoforduration', data=data)

    def swipe_left(self):
        w, h = self.window_size()
        return self.swipe(w, h // 2, 0, h // 2)

    def swipe_right(self):
        w, h = self.window_size()
        return self.swipe(0, h // 2, w, h // 2)

    def swipe_up(self):
        w, h = self.window_size()
        return self.swipe(w // 2, h, w // 2, 0)

    def swipe_down(self):
        w, h = self.window_size()
        return self.swipe(w // 2, 0, w // 2, h)

    @property
    def orientation(self):
        """
        Return string
        One of <PORTRAIT | LANDSCAPE>
        """
        return self._session_http.get('orientation').value

    @orientation.setter
    def orientation(self, value):
        """
        Args:
            - orientation(string): LANDSCAPE | PORTRAIT | UIA_DEVICE_ORIENTATION_LANDSCAPERIGHT |
                    UIA_DEVICE_ORIENTATION_PORTRAIT_UPSIDEDOWN
        """
        return self._session_http.post('orientation', data={'orientation': value})

    def window_size(self):
        """
        Returns:
            namedtuple: eg
                Size(width=320, height=568)
        """
        value = self._session_http.get('/window/size').value
        w = roundint(value['width'])
        h = roundint(value['height'])
        return namedtuple('Size', ['width', 'height'])(w, h)

    def send_keys(self, value):
        """
        send keys, yet I know not, todo function
        """
        if isinstance(value, six.string_types):
            value = list(value)
        return self._session_http.post('/wda/keys', data={'value': value})

    def keyboard_dismiss(self):
        """
        Not working for now
        """
        raise RuntimeError("not pass tests, this method is not allowed to use")
        self._session_http.post('/wda/keyboard/dismiss')

    def xpath(self, value):
        """
        For weditor, d.xpath(...)
        """
        httpclient = self._session_http.new_client('')
        return Selector(httpclient, self, xpath=value)

    @property
    def alert(self):
        return Alert(self)

    def close(self): # close session
        return self._session_http.delete('/')

    def __call__(self, *args, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.__timeout
        return Selector(self._session_http, self, *args, **kwargs)
    
    @property
    def alibaba(self):
        """ Only used in alibaba company """
        try:
            import wda_taobao
            return wda_taobao.Alibaba(self)
        except ImportError:
            raise RuntimeError(
                "@alibaba property requires wda_taobao library installed")

    @property
    def taobao(self):
        try:
            import wda_taobao
            return wda_taobao.Taobao(self)
        except ImportError:
            raise RuntimeError(
                "@taobao property requires wda_taobao library installed")


Session = Client # for compability

class Alert(object):
    def __init__(self, client):
        self._c = client
        self.http = client.http

    @property
    def exists(self):
        try:
            self.text
        except WDARequestError as e:
            if e.status != 27:
                raise
            return False
        return True

    @property
    def text(self):
        return self.http.get('/alert/text').value
        # return self._c._session_http.get('/alert/text').value

    def wait(self, timeout=20.0):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.exists:
                return True
            time.sleep(0.2)
        return False

    def accept(self):
        return self.http.post('/alert/accept')

    def dismiss(self):
        return self.http.post('/alert/dismiss')

    def buttons(self):
        return self._c._session_http.get('/wda/alert/buttons').value
        # return self.http.get('/wda/alert/buttons').value

    def click(self, button_name):
        """
        Args:
            - button_name: the name of the button
        """
        # Actually, It has no difference POST to accept or dismiss
        return self.http.post('/alert/accept', data={"name": button_name})

class Selector(object):
    def __init__(self,
                 httpclient,
                 session,
                 predicate=None,
                 id=None,
                 className=None,
                 type=None,
                 name=None,
                 nameContains=None,
                 nameMatches=None,
                 text=None,
                 textContains=None,
                 textMatches=None,
                 value=None,
                 valueContains=None,
                 valueMatches=None,
                 label=None,
                 labelContains=None,
                 visible=None,
                 enabled=None,

                 # https://github.com/facebookarchive/WebDriverAgent/wiki/Predicate-Queries-Construction-Rules
                 #  rect - Element's rectangle as a dictionary with the following keys: x, y, width, height
                 rect=None,
                 x=None,
                 y=None,
                 width=None,
                 height=None,

                 classChain=None,
                 xpath=None,
                 parent_class_chains=[],
                 timeout=10.0,
                 index=0):
        '''
        Args:
            predicate (str): predicate string
            id (str): raw identifier
            className (str): attr of className
            type (str): alias of className
            name (str): attr for name
            nameContains (str): attr of name contains
            nameMatches (str): regex string
            text (str): alias of name
            textContains (str): alias of nameContains
            textMatches (str): alias of nameMatches
            value (str): attr of value, not used in most times
            valueContains (str): attr of value contains
            valueMatches (str): attr of value regex string
            label (str): attr for label
            labelContains (str): attr for label contains
            visible (bool): is visible
            enabled (bool): is enabled
            rect (dict):  Element's rectangle as a dictionary with the following keys: x, y, width, height
            x (int/str):  x of rect
            y (int/str):  y of rect
            width (int/str):  width of rect
            height (int/str):  height of rect
            classChain (str): string of ios chain query, eg: **/XCUIElementTypeOther[`value BEGINSWITH 'blabla'`]
            xpath (str): xpath string, a little slow, but works fine
            timeout (float): maxium wait element time, default 10.0s
            index (int): index of founded elements
        
        WDA use two key to find elements "using", "value"
        Examples:
        "using" can be on of 
            "partial link text", "link text"
            "name", "id", "accessibility id"
            "class name", "class chain", "xpath", "predicate string"
        
        predicate string support many keys
            UID,
            accessibilityContainer,
            accessible,
            enabled,
            frame,
            label,
            name,
            rect,
            type,
            value,
            visible,
            wdAccessibilityContainer,
            wdAccessible,
            wdEnabled,
            wdFrame,
            wdLabel,
            wdName,
            wdRect,
            wdType,
            wdUID,
            wdValue,
            wdVisible
        '''
        if DEBUG:
            print("Selector __init__: httpclient=%s, session=%s, predicate=%s, id=%s" % (httpclient, session, predicate, id))
            print("Selector __init__: className=%s, type=%s, name=%s, nameContains=%s, nameMatches=%s" % (className, type, name, nameContains, nameMatches))
            print("Selector __init__: text=%s, textContains=%s, textMatches=%s, value=%s, valueContains=%s, valueMatches=%s" % (text, textContains, textMatches, value, valueContains, valueMatches))
            print("Selector __init__: label=%s, labelContains=%s, visible=%s, value=%s, enabled=%s" % (label, labelContains, visible, value, enabled))
            print("Selector __init__: rect=%s, x=%s, y=%s, width=%s, height=%s" % (rect, x, y, width, height))
            print("Selector __init__: classChain=%s, xpath=%s, parent_class_chains=%s, timeout=%s, index=%s" % (classChain, xpath, parent_class_chains, timeout, index))

        self.http = httpclient
        self.session = session

        self.predicate = predicate
        self.id = id
        self.class_name = className or type
        self.name = self._add_escape_character_for_quote_prime_character(
            name or text)
        self.name_part = nameContains or textContains
        self.name_regex = nameMatches or textMatches
        self.value = value
        self.value_part = valueContains
        self.value_regex = valueMatches
        self.label = label
        self.label_part = labelContains

        # self.enabled = enabled
        # self.visible = visible
        # self.enabled = self._toBool(enabled)
        # self.visible = self._toBool(visible)
        if enabled is not None:
            self.enabled = self._toBool(enabled)
        else:
            self.enabled = None

        if visible is not None:
            self.visible = self._toBool(visible)
        else:
            self.visible = None

        if rect:
            self.rect = rect
        else:
            self.rect = None

            rectDict = {}

            if x:
                self.x = int(x)
                rectDict["x"] = self.x
            if y:
                self.y = int(y)
                rectDict["y"] = self.y
            if width:
                self.width = int(width)
                rectDict["width"] = self.width
            if height:
                self.height = int(height)
                rectDict["height"] = self.height

            if rectDict:
                self.rect = rectDict

        self.index = index

        self.xpath = self._fix_xcui_type(xpath)
        self.class_chain = self._fix_xcui_type(classChain)
        self.timeout = timeout
        # some fixtures
        if self.class_name and not self.class_name.startswith(
                'XCUIElementType'):
            self.class_name = 'XCUIElementType' + self.class_name
        if self.name_regex:
            if not self.name_regex.startswith(
                    '^') and not self.name_regex.startswith('.*'):
                self.name_regex = '.*' + self.name_regex
            if not self.name_regex.endswith(
                    '$') and not self.name_regex.endswith('.*'):
                self.name_regex = self.name_regex + '.*'
            if DEBUG:
                print("after update: self.name_regex=%s" % self.name_regex)
        self.parent_class_chains = parent_class_chains
    
    def _toBool(self, inputValue):
        respBool = False
        if isinstance(inputValue, bool):
            respBool = inputValue
        elif isinstance(inputValue, str):
            lowerStr = inputValue.lower()
            TrueStrList = ["true", "yes", "1"]
            if lowerStr in TrueStrList:
                respBool = True
        elif isinstance(inputValue, int):
            if inputValue >= 1:
                respBool = True

        if DEBUG:
            print("inputValue=%s -> respBool=%s" % (inputValue, respBool))

        return respBool

    def _fix_xcui_type(self, s):
        if s is None:
            return
        re_element = '|'.join(xcui_element_types.ELEMENTS)
        return re.sub(r'/(' + re_element + ')', '/XCUIElementType\g<1>', s)

    def _add_escape_character_for_quote_prime_character(self, text):
        """
        Fix for https://github.com/openatx/facebook-wda/issues/33
        Returns:
            string with properly formated quotes, or non changed text
        """
        if text is not None:
            if "'" in text:
                return text.replace("'", "\\'")
            elif '"' in text:
                return text.replace('"', '\\"')
            else:
                return text
        else:
            return text

    def _wdasearch_single(self, using, value):
        """
        Returns:
            bool, str
                True, element info:
                    {
                        "id": "0F000000-0000-0000-D703-000000000000",
                        "name": "通讯录",
                        "value": None,
                        "text": "通讯录",
                        "label": "通讯录",
                        "rect": {
                            "y": 619,
                            "x": 96,
                            "width": 90,
                            "height": 48
                        },
                        "type": "XCUIElementTypeButton"
                    }

                False, error info: 
                    {
                        "error" : "no such element",
                        "message" : "unable to find an element using 'class chain', value '**\/XCUIElementTypeAny[`name == '搜索'`]'",
                        "traceback" : "(\n\t0   WebDriverAgentLib                   0x0000000100f011ec FBNoSuchElementErrorResponseForRequest....... 4\n)"
                    }
        """
        isFound, respInfo = False, "Unknown error"

        postDict = {
            'using': using,
            'value': value
        }

        if DEBUG:
            print("postDict=%s" % postDict)

        isException = False
        # resp = self.http.post('/element', postDict)
        try:
            resp = self.http.post('/element', postDict)
        except WDARequestError as wdaReqErr:
            isException = True
            if DEBUG:
                print("wdaReqErr=%s" % wdaReqErr)

            errCode = wdaReqErr.status
            errMsg = wdaReqErr.value
            errorInfo = {
                "error": errCode,
                "message": errMsg
            }
            respInfo = errorInfo
        
        if not isException:
            # if DEBUG:
            #     print("postDict=%s -> resp=%s" % (postDict, resp))

            respValue = resp.value
            # if DEBUG:
            #     print("respValue=%s" % respValue)

            respValueKeys = respValue.keys()
            hasError = "error" in respValueKeys
            hasMessage = "message" in respValueKeys
            isError = hasError and hasMessage

            if isError:
                """
                {
                    "value" : {
                        "error" : "no such element",
                        "message" : "unable to find an element using 'class chain', value '**\/XCUIElementTypeAny[`name == '搜索'`]'",
                        "traceback" : "(\n\t0   WebDriverAgentLib    0x0000000100f011ec FBNoSuchElementErrorResponseForRequest....... 4\n)"
                    },
                    "sessionId" : "DCF1A843-9FB9-4415-9A7C-8AF4ACDC3046"
                }
                """
                isFound = False
                errorInfo = respValue
                respInfo = errorInfo
            else:
                isFound = True
                elementId = respValue['ELEMENT']
                # if DEBUG:
                #     print("elementId=%s" % elementId)

                """
                {
                    "value" : {
                        "text" : null,
                        "element-6066-11e4-a52e-4f735466cecf" : "00000000-0000-0000-0000-000000000000",
                        "label" : null,
                        "attribute\/name" : null,
                        "attribute\/value" : null,
                        "ELEMENT" : "00000000-0000-0000-0000-000000000000"
                    },
                    "sessionId" : "E649E60F-16A1-48D4-8840-67387787A0A2"
                }
                """
                EmptyId = "00000000-0000-0000-0000-000000000000"

                if elementId == EmptyId:
                    isFound = False
                    respInfo = {
                        "error" : "empty id",
                        "message" : "found element but id is empty %s from %s" % (EmptyId, str(postDict)),
                    }
                else:
                    """
                    {
                        "value" : {
                            "element-6066-11e4-a52e-4f735466cecf" : "19010000-0000-0000-A303-000000000000",
                            "attribute/name" : "添加",
                            "attribute/value" : null,
                            "text" : "添加",
                            "label" : "添加",
                            "rect" : {
                                "y" : 20,
                                "x" : 317,
                                "width" : 58,
                                "height" : 44
                            },
                            "type" : "XCUIElementTypeButton",
                            "name" : "XCUIElementTypeButton",
                            "ELEMENT" : "19010000-0000-0000-A303-000000000000"
                        },
                        "sessionId" : "DCF1A843-9FB9-4415-9A7C-8AF4ACDC3046"
                    }
                    """
                    elementInfo = {
                        "id": elementId
                    }
                    # respKeyList = ["type","label","name","text","rect","attribute/name","attribute/value"]
                    # mapKeyList =  ["type","label",    "","text","rect",          "name",          "value"]
                    respKeyMap = {
                        "type": "type",
                        "label": "label",
                        "name": None,
                        "text": "text",
                        "rect": "rect",
                        "attribute/name": "name",
                        "attribute/value": "value",
                    }

                    for eachKey in respValueKeys:
                        if eachKey in respKeyMap.keys():
                            eachValue = respValue[eachKey]
                            mapRealKey = respKeyMap[eachKey]
                            if mapRealKey:
                                elementInfo[mapRealKey] = eachValue

                    respInfo = elementInfo

        if DEBUG:
            print("isFound=%s, respInfo=%s" % (isFound, respInfo))

        # return elementId
        return isFound, respInfo

    def _wdasearch(self, using, value):
        """
        Returns:
            element_ids (list(string)): example ['id1', 'id2']
        
        HTTP example response:
        [
            {"ELEMENT": "E2FF5B2A-DBDF-4E67-9179-91609480D80A"},
            {"ELEMENT": "597B1A1E-70B9-4CBE-ACAD-40943B0A6034"}
        ]
        """
        if DEBUG:
            print("using=%s, value=%s" % (using, value))

        element_ids = []
        # for v in self.http.post('/elements', {
        #         'using': using,
        #         'value': value
        # }).value:
        #     element_ids.append(v['ELEMENT'])
        resp = self.http.post('/elements', {
                'using': using,
                'value': value
        })
        valueList = resp.value

        if DEBUG:
            print("valueList=%s" % valueList)

        for eachValue in valueList:
            eachElement = eachValue['ELEMENT']
            element_ids.append(eachElement)

        if DEBUG:
            print("element_ids=%s" % element_ids)

        return element_ids

    def _gen_class_chain(self):
        # just return if aleady exists predicate
        if self.predicate:
            return '/XCUIElementTypeAny[`' + self.predicate + '`]'
        qs = []
        if self.name:
            qs.append("name == '%s'" % self.name)
        if self.name_part:
            qs.append("name CONTAINS '%s'" % self.name_part)
        if self.name_regex:
            # escapedNameRegex = self.name_regex.encode('unicode_escape')
            # if DEBUG:
            #     print("self.name_regex=%s, escapedNameRegex=%s" % (self.name_regex, escapedNameRegex))
            # qs.append("name MATCHES '%s'" % escapedNameRegex)
            qs.append("name MATCHES '%s'" % self.name_regex)
            if DEBUG:
                print("after add name_regex: qs=%s" % qs)
        if self.label:
            qs.append("label == '%s'" % self.label)
        if self.label_part:
            qs.append("label CONTAINS '%s'" % self.label_part)
        if self.value:
            qs.append("value == '%s'" % self.value)
        if self.value_part:
            # qs.append("value CONTAINS ’%s'" % self.value_part)
            qs.append("value CONTAINS '%s'" % self.value_part)
        if self.value_regex:
            # escapedValueRegex = self.value_regex.encode('unicode_escape')
            # if DEBUG:
            #     print("self.value_regex=%s, escapedValueRegex=%s" % (self.value_regex, escapedValueRegex))
            # qs.append("value MATCHES '%s'" % escapedValueRegex)
            qs.append("value MATCHES '%s'" % self.value_regex)
            if DEBUG:
                print("after add value_regex: qs=%s" % qs)

        # BoolTrueValue = "true"
        # BoolFalseValue = "false"
        BoolTrueValue = "1"
        BoolFalseValue = "0"

        if self.enabled is not None:
            enabledValue = BoolTrueValue if self.enabled else BoolFalseValue
            enableKey = "enabled"
            # enableKey = "wdEnabled"
            qs.append("%s == %s" % (enableKey, enabledValue))

        # 20200427: after merge latest WebDriverAgent, continue test visible
        if DEBUG:
            print("self.visible=%s" % self.visible)
        if self.visible is not None:
            visibleKey = "visible"
            # Note: WebDriverAgent says support visible, but actually not support visible
            #   so temp change to (maybe similar meaning) accessible
            # 20200402: sometime use visible or accessible can NOT found element, so not use it
            # visibleKey = "accessible"
            # 20200408: debug displayed
            # visibleKey = "displayed"
            visibleValue =  BoolTrueValue if self.visible else BoolFalseValue
            visibleConditionStr = "%s == %s" % (visibleKey, visibleValue)
            qs.append(visibleConditionStr)
            if DEBUG:
                print("visibleConditionStr=%s" % visibleConditionStr)
                print("qs=%s" % qs)

        if self.rect:
            rectKeyList = ["x", "y", "width", "height"]
            for eachRectKey in rectKeyList:
                if eachRectKey in self.rect.keys():
                    eachRectValue = self.rect[eachRectKey]
                    curMatchRule = "rect.%s == %s" % (eachRectKey, eachRectValue)
                    qs.append(curMatchRule)

        predicate = ' AND '.join(qs)
        chain = '/' + (self.class_name or 'XCUIElementTypeAny')

        if predicate:
            chain = chain + '[`' + predicate + '`]'
        if self.index:
            chain = chain + '[%d]' % self.index

        if DEBUG:
            print("generated class chain=%s" % chain)

        return chain

    def find_element_ids(self):
        elems = []
        if self.id:
            return self._wdasearch('id', self.id)
        if self.predicate:
            return self._wdasearch('predicate string', self.predicate)
        if self.xpath:
            return self._wdasearch('xpath', self.xpath)
        if self.class_chain:
            return self._wdasearch('class chain', self.class_chain)

        chain = '**' + ''.join(
            self.parent_class_chains) + self._gen_class_chain()
        if DEBUG:
            print('CHAIN: %s', chain)
        return self._wdasearch('class chain', chain)

    def find_element_id(self):
        if self.id:
            return self._wdasearch_single('id', self.id)

        if self.predicate:
            if DEBUG:
                print('PREDICATE: %s', self.predicate)
            return self._wdasearch_single('predicate string', self.predicate)

        if self.xpath:
            if DEBUG:
                print('XPATH: %s', self.xpath)
            return self._wdasearch_single('xpath', self.xpath)

        if self.class_chain:
            if DEBUG:
                print('CLASS_CHAIN: %s', self.class_chain)
            return self._wdasearch_single('class chain', self.class_chain)

        chain = '**' + ''.join(
            self.parent_class_chains) + self._gen_class_chain()
        if DEBUG:
            print('CHAIN: %s', chain)
        return self._wdasearch_single('class chain', chain)

    def find_element(self):
        """
        Returns:
            True, Element: single element
            False, error info
        """
        # element = None
        # elementId = self.find_element_id()
        isFound, respInfo = self.find_element_id()

        if DEBUG:
            # print('elementId=%s' % elementId)
            print('isFound=%s, respInfo=%s' % (isFound, respInfo))

        if isFound:
            elementInfo = respInfo
            elementId = elementInfo["id"]

            # add bounds support
            curBounds = None
            if "rect" in elementInfo:
                rectDict = elementInfo["rect"]
                x = rectDict["x"]
                y = rectDict["y"]
                width = rectDict["width"]
                height = rectDict["height"]
                curBounds = Rect(x, y, width, height)
            if DEBUG:
                print("curBounds=%s" % curBounds)

            # element = Element(self.http.new_client(''), elementId, rect=curRect)
            element = Element(self.http.new_client(''), elementId, bounds=curBounds)

            if DEBUG:
                print('element=%s' % element)

            respInfo = element

        return isFound, respInfo

    def find_elements(self):
        """
        Returns:
            Element (list): all the elements
        """
        es = []
        for element_id in self.find_element_ids():
            if DEBUG:
                print('find_elements: element_id=%s' % element_id)
            ele = Element(self.http.new_client(''), element_id)
            if DEBUG:
                print('find_elements: ele=%s' % ele)
            es.append(ele)
        return es

    def count(self):
        if DEBUG:
            print("count")
        
        elementIdList = self.find_element_ids()
        elementIdNum = len(elementIdList)

        if DEBUG:
            print("count: elementIdList=%s" % elementIdList)

        return elementIdNum

    # def get(self, timeout=None, raise_error=True, isRespSingle=False):
    # def get(self, timeout=None, raise_error=True, isRespSingle=True):
    def get(self, timeout=None):
        """
        Args:
            timeout (float): timeout for query element, unit seconds
                Default 10s

        Returns:
            True, Element
            False, error info

        Raises:
        """
        isFound, respInfo = False, "Unknown error"

        if DEBUG:
            # print("get: timeout=%s, raise_error=%s, isRespSingle=%s" % (timeout, raise_error, isRespSingle))
            print("get: timeout=%s" % timeout)

        start_time = time.time()
        if timeout is None:
            timeout = self.timeout

        if DEBUG:
            print("get: timeout=%s" % timeout)

        endTime = start_time + timeout
        while True:
            # if isRespSingle:
            #     singleElement = self.find_element()
            #     if singleElement:
            #         return singleElement
            # else:
            #     elems = self.find_elements()
            #     if len(elems) > 0:
            #         return elems[0]
            isFound, respInfo = self.find_element()
            if isFound:
                return isFound, respInfo

            curTime = time.time()
            if endTime < curTime:
                break

            # time.sleep(0.01)
            time.sleep(RETRY_INTERVAL)

            if DEBUG:
                from datetime import datetime
                curDatetime = datetime.fromtimestamp(float(curTime))
                print("curDatetime=%s -> Not timeout, continue find" % curDatetime)

        # # check alert again
        # sessionAlertExists = self.session.alert.exists
        # httpAlertCallback = self.http.alert_callback

        # if DEBUG:
        #     print("get: sessionAlertExists=%s, httpAlertCallback=%s" % (sessionAlertExists, httpAlertCallback))

        # if sessionAlertExists and httpAlertCallback:
        #     self.http.alert_callback()

        #     if DEBUG:
        #         print("get: timeout=%s, raise_error=%s" % (timeout, raise_error))

        #     # return self.get(timeout, raise_error)
        #     return self.get(timeout)

        # if raise_error:
        #     raise WDAElementNotFoundError("element not found", "timeout %.1f" % timeout)
        return isFound, respInfo

    def __getattr__(self, oper):
        if DEBUG:
            print("oper=%s" % oper)

        # return getattr(self.get(), oper)
        isFound, respInfo = self.get()

        if DEBUG:
            print("isFound=%s, respInfo=%s" % (isFound, respInfo))

        if isFound:
            element = respInfo
            return getattr(element, oper)
        else:
            return None

    def set_timeout(self, s):
        """
        Set element wait timeout
        """
        self.timeout = s
        return self

    def __getitem__(self, index):
        self.index = index
        return self

    def child(self, *args, **kwargs):
        chain = self._gen_class_chain()
        kwargs['parent_class_chains'] = self.parent_class_chains + [chain]
        return Selector(self.http, self.session, *args, **kwargs)

    @property
    def exists(self):
        return len(self.find_element_ids()) > self.index

    def click_exists(self, timeout=0):
        """
        Wait element and perform click

        Args:
            timeout (float): timeout for wait
        
        Returns:
            bool: if successfully clicked
        """
        # e = self.get(timeout=timeout, raise_error=False)
        # if e is None:
        #     return False
        isFound, respInfo = self.get(timeout=timeout)
        if isFound:
            e = respInfo

            e.click()
            return True
        else:
            return False

    # def wait(self, timeout=None, raise_error=True):
    def wait(self, timeout=None):
        """ alias of get
        Args:
            timeout (float): timeout seconds
        
        Raises:
        """
        # return self.get(timeout=timeout, raise_error=raise_error)
        return self.get(timeout=timeout)

    def wait_gone(self, timeout=None, raise_error=True):
        """
        Args:
            timeout (float): default timeout
            raise_error (bool): return bool or raise error
        
        Returns:
            bool: works when raise_error is False

        Raises:
            WDAElementNotDisappearError
        """
        start_time = time.time()
        if timeout is None or timeout <= 0:
            timeout = self.timeout
        while start_time + timeout > time.time():
            if not self.exists:
                return True
        if not raise_error:
            return False
        raise WDAElementNotDisappearError("element not gone")

    # todo
    # pinch
    # touchAndHold
    # dragfromtoforduration
    # twoFingerTap

    # todo
    # handleGetIsAccessibilityContainer
    # [[FBRoute GET:@"/wda/element/:uuid/accessibilityContainer"] respondWithTarget:self action:@selector(handleGetIsAccessibilityContainer:)],


class Element(object):
    # def __init__(self, httpclient, id):
    # def __init__(self, httpclient, id, rect=None):
    def __init__(self, httpclient, id, bounds=None):
        """
        base_url eg: http://localhost:8100/session/$SESSION_ID
        """
        self.http = httpclient
        self._id = id
        # add cached rect=bounds, to avoid later get rect but return 0
        if DEBUG:
            print("bounds=%s" % bounds)
        if bounds:
            self.bounds = bounds
            if DEBUG:
                print("use pass in bounds=%s" % self.bounds)

    def __repr__(self):
        return '<wda.Element(id="{}")>'.format(self.id)

    def _req(self, method, url, data=None):
        return self.http.fetch(method, '/element/' + self.id + url, data)

    def _wda_req(self, method, url, data=None):
        return self.http.fetch(method, '/wda/element/' + self.id + url, data)

    def _prop(self, key):
        return self._req('get', '/' + key.lstrip('/')).value

    def _wda_prop(self, key):
        ret = self._request('GET', 'wda/element/%s/%s' % (self._id, key)).value
        return ret

    # @property
    @cached_property
    def id(self):
        return self._id

    # @property
    @cached_property
    def label(self):
        return self._prop('attribute/label')

    # @property
    @cached_property
    def className(self):
        return self._prop('attribute/type')

    # @property
    @cached_property
    def text(self):
        return self._prop('text')

    # @property
    @cached_property
    def name(self):
        # return self._prop('name')
        # Note: here property name, internally: FBElementCommands.m -> handleGetName -> use wdType
        # so, for:
        # <XCUIElementTypeButton type="XCUIElementTypeButton" name="¥1.00" label="¥1.00" enabled="true" visible="true" x="154" y="152" width="74" height="30"/>
        # name is XCUIElementTypeButton in type="XCUIElementTypeButton"
        # not expected: ¥1.00 in name="¥1.00"
        # so change to 'attribute/name'
        return self._prop('attribute/name') # ¥1.00

    # @property
    @cached_property
    def displayed(self):
        return self._prop("displayed")

    # @property
    @cached_property
    def enabled(self):
        return self._prop('enabled')

    # @property
    @cached_property
    def accessible(self):
        return self._wda_prop("accessible")
        # return self._prop("accessible")

    # @property
    @cached_property
    def accessibility_container(self):
        return self._wda_prop('accessibilityContainer')
        # return self._prop('accessibilityContainer')

    @property
    # Special: not used cache value for AppStore downloading element value will changed
    #   <XCUIElementTypeButton type="XCUIElementTypeButton" value="18%" name="正在下载" label="正在下载" enabled="true" visible="true" x="154" y="308" width="74" height="30"/>
    #   if use cache, later always get None
    # @cached_property
    def value(self):
        curValue = self._prop('attribute/value')
        # curValue = self._prop('attribute/wdValue')
        if DEBUG:
            print("curValue=%s" % curValue)
        return curValue

    # @property
    @cached_property
    def enabled(self):
        return self._prop('enabled')

    # @property
    @cached_property
    def visible(self):
        # if DEBUG:
        #     print("call attribute/visible to get visible value")
        return self._prop('attribute/visible')

    # @property
    @cached_property
    def bounds(self):
        if DEBUG:
            print("try get Element bounds=rect")

        value = self._prop('rect')
        x, y = value['x'], value['y']
        w, h = value['width'], value['height']
        rectObj = Rect(x, y, w, h)
        if DEBUG:
            print("rectObj=%s" % rectObj)
        return rectObj

    # operations
    def tap(self):
        return self._req('post', '/click')

    def click(self):
        """ Alias of tap """
        return self.tap()

    def tap_hold(self, duration=1.0):
        """
        Tap and hold for a moment

        Args:
            duration (float): seconds of hold time

        [[FBRoute POST:@"/wda/element/:uuid/touchAndHold"] respondWithTarget:self action:@selector(handleTouchAndHold:)],
        """
        return self._wda_req('post', '/touchAndHold', {'duration': duration})

    def scroll(self, direction='visible', distance=1.0):
        """
        Args:
            direction (str): one of "visible", "up", "down", "left", "right"
            distance (float): swipe distance, only works when direction is not "visible"
               
        Raises:
            ValueError

        distance=1.0 means, element (width or height) multiply 1.0
        """
        if direction == 'visible':
            self._wda_req('post', '/scroll', {'toVisible': True})
        elif direction in ['up', 'down', 'left', 'right']:
            self._wda_req('post', '/scroll', {
                'direction': direction,
                'distance': distance
            })
        else:
            raise ValueError("Invalid direction")
        return self

    def pinch(self, scale, velocity):
        """
        Args:
            scale (float): scale must > 0
            velocity (float): velocity must be less than zero when scale is less than 1
        
        Example:
            pinchIn  -> scale:0.5, velocity: -1
            pinchOut -> scale:2.0, velocity: 1
        """
        data = {'scale': scale, 'velocity': velocity}
        return self._wda_req('post', '/pinch', data)

    def set_text(self, value):
        return self._req('post', '/value', {'value': value})

    def clear_text(self):
        return self._req('post', '/clear')

    # def child(self, **kwargs):
    #     return Selector(self.__base_url, self._id, **kwargs)

    # todo lot of other operations
    # tap_hold
