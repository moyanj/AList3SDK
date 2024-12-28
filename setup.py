from setuptools import setup, find_packages

setup(
    name="alist3",
    version="1.3.4",
    description="AListV3 PythonSDK",
    author="MoYan",
    author_email="moyanjdc@qq.com",
    packages=find_packages(),
    long_description=open("readme.md").read(),  # 包的详细描述
    long_description_content_type="text/markdown",  # 描述的内容类型
    install_requires=[
        "aiohttp",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Utilities",
        "Natural Language :: English",
        "Natural Language :: Chinese (Simplified)",
    ],
    include_package_data=True,
)
