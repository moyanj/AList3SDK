from setuptools import setup, find_packages

setup(
    name="alist3",
    version="1.3.0",
    description="AListV3 PythonSDK",
    author="MoYan",
    packages=find_packages(),
    long_description=open("readme.md").read(),  # 包的详细描述
    long_description_content_type="text/markdown",  # 描述的内容类型
    install_requires=[
        # 添加你的依赖库
        "aiohttp",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
        "Natural Language :: English",
        "Natural Language :: Chinese (Simplified)"
    ]
)
