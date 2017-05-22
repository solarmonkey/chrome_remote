from setuptools import setup, find_packages

setup(
    name='chrome_remote',
    version='1.0.0',
    description="Python Wrapper fully for the Google Chrome Remote Debugging Protocol",
    author='Yifei Kong',
    packages=find_packages(),
    install_requires=['requests', 'websocket-client']
)
