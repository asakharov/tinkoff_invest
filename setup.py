from setuptools import setup

setup(
    name='tinkoff_invest',
    version='1.0.1',
    packages=['tinkoff_invest', 'tinkoff_invest.models'],
    url='https://github.com/asakharov/tinkoff_invest',
    python_requires='>=3.8.0',
    install_requires=[
        "prettytable", "iso8601", "requests", "ujson", "urllib3", "websocket-client"
    ],
    license='MIT',
    author='Alexey Sakharov',
    author_email='alexey.sakharov@gmail.com',
    description='Client library for Tinkoff broker'
)
