# Chrome Remote

Simple wrapper to drive full Google Chrome from Python using the [Remote Debugging Protocol](https://chromedevtools.github.io/devtools-protocol)

This package implenments all methods in chrome devtools protocol, but the events are not implenmented.

## Installation

    $ pip install git+https://github.com/yifeikong/chrome_remote.git

## API

```python
>>> from chrome_remote import Chrome
>>> chrome = Chrome()
>>> chrome.start_chrome()  # if chrome has not been started
>>> tab = chrome.get_tabs()[0]
>>> tab.goto('http://zhihu.com/')
>>> tab.get_html()
# ... html content of given site
```

## License

MIT
