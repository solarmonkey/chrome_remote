# -*- coding: utf-8 -*-

"""
Chrome Remote

Python wrapper for Google Chrome Remote Debugging Protocol

https://chromedevtools.github.io/devtools-protocol/
"""


import re
import json
import requests
import websocket
from requests.exceptions import ConnectionError
import subprocess


__version__ = "1.0.0"
__all__ = ['Chrome', 'ChromeTab']


class ChromeConnectionError(ConnectionError):
    pass


class ChromeResponseError(ValueError):
    pass


def compact(iterable):
    """
    >>> list(compact([0, 1, 2]))
    [1, 2]
    >>> list(compact([1, 2]))
    [1, 2]
    >>> list(compact([0, 1, False, 2, '', 3]))
    [1, 2, 3]
    """
    for el in iterable:
        if el:
            yield el


def pascal_case(s):
    """convert token(s) to PascalCase
    >>> pascal_case('fooBar')
    'FooBar'
    >>> pascal_case('foo_bar')
    'FooBar'
    >>> pascal_case('foo-bar')
    'FooBar'
    >>> pascal_case('FooBar')
    'FooBar'
    >>> pascal_case('Foo-Bar')
    'FooBar'
    >>> pascal_case('foo bar')
    'FooBar'
    """
    s = re.sub(r'[A-Z]', r'-\g<0>', s, flags=re.UNICODE)  # turing uppercase to seperator with lowercase
    s = s.replace('_', '-')
    words = compact(re.split(r'\W+', s, flags=re.UNICODE))
    return ''.join([word.lower().capitalize() for word in words])


def camel_case(s):
    """convert token(s) to camelCase
    >>> camel_case('fooBar')
    'fooBar'
    >>> camel_case('foo_bar')
    'fooBar'
    >>> camel_case('foo-bar')
    'fooBar'
    >>> camel_case('FooBar')
    'fooBar'
    >>> camel_case('Foo-Bar')
    'fooBar'
    >>> camel_case('foo bar')
    'fooBar'
    """
    if s:
        s = pascal_case(s)
        s = s[0].lower() + s[1:]
    return s


class ChromeTab(object):

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.title = kwargs.get('title')
        self.url = kwargs.get('url')
        self.type = kwargs.get('type')
        self.websocket_url = kwargs.get('webSocketDebuggerUrl')

    def __getattr__(self, name):
        """
        Calling chrome api via meta method

        e.g.
        >>> tab = ChromeTab(...)
        >>> tab.page__navigate(url='http://google.com')  # calls Page.navigate method in chrome remote api
        """
        def _chrome_api(**kwargs):  # NOTE *args not allowed
            # construct calling dict
            domain, fn = name.split('__', 1)
            domain = pascal_case(domain).replace('Dom', 'DOM')
            fn = camel_case(fn)
            params = {camel_case(k).replace('Http', 'HTTP'): v for k, v in kwargs.items()}
            message = {'id': 1, 'method': '{0}.{1}'.format(domain, fn), 'params': params}

            # send the request
            ws = websocket.create_connection(self.websocket_url)
            ws.send(json.dumps(message))
            res = json.loads(ws.recv())
            ws.close()
            return res.get('result')
        return _chrome_api

    def run_js(self, js_expr):
        return self.runtime__evaluate(expression=js_expr)

    def get_html(self):
        result = self.run_js('document.documentElement.outerHTML')
        value = result['value']
        return value.encode('utf-8')

    def reload(self):
        return self.page__reload()

    def goto(self, url):
        return self.page__navigate(url=url)

    def set_user_agent(self, user_agent):
        return self.network__set_user_agent_override(user_agent=user_agent)

    def add_headers(self, headers):
        return self.network__set_extra_http_headers(headers=headers)

    def clear_cache(self):
        return self.network__clear_browser_cache()

    def clear_cookies(self):
        return self.network__clear_browser_cookies()

    def __str__(self):
        return '[%s - %s]' % (self.title, self.url)

    __repr__ = __str__


class Chrome(object):

    def __init__(self, host='localhost', port=9222):
        self.host = host
        self.port = port
        self.api = 'http://%s:%d' % (self.host, self.port)

    def _access_api(self, url):
        try:
            r = requests.get(url)
            return r.json()
        except ConnectionError:
            raise ChromeConnectionError("Connect error! is Chrome running with --remote-debugging-port=%d?" % self.port)

    def get_tabs(self):
        """
        Get all open browser tabs that are pages tabs
        """
        tabs = self._access_api(self.api + '/json')
        return [ChromeTab(**tab) for tab in tabs if tab['type'] == 'page']

    def create_tab(self, url):
        """
        Open a new tab page
        """
        r = self._access_api(self.api + '/json/new?' + url)
        return ChromeTab(**r)

    def close_tab(self, tab):
        """
        Close the given tab
        """
        self._access_api('{api}/json/close/{tab_id}'.format(api=self.api, tab_id=tab.id))

    def activate_tab(self, tab):
        """
        Activate the given tab
        """
        self._access_api('{api}/json/activate/{tab_id}'.format(api=self.api, tab_id=tab.id))

    def start_chrome(self):
        """
        Start the chrome browser
        """
        self.chrome_process = subprocess.Popen(['google-chrome', \
                '--headless', \
                '--disable-gpu', \
                '--remote-debugging-port=9222', \
                '--js-flags="--max_old_space_size=512"', \
        ], shell=True)

    def __len__(self):
        return len(self.tabs)

    def __str__(self):
        return '[Chromote(tabs=%d)]' % len(self)

    def __repr__(self):
        return 'Chromote(host="%s", port=%s)' % (self.host, self.port)

