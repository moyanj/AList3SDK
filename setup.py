from setuptools import setup, find_packages
import time

setup(
    name="alist3",
    version="1.0",
    description="AListV3 PythonSDK",
    author="MoYan",
    packages=find_packages(),
    install_requires=[
        # 添加你的依赖库
        "requests",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
