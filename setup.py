from setuptools import setup

setup(
    name="beets-gogdplex",
    version="0.1",
    description="beets plugin to create Grateful Dead playlists",
    long_description=open("README.md").read(),
    author="Ross Hendry ",
    author_email="rhendry@gmail.com",
    url="https://github.com/chooban/beets-gogd",
    license="MIT",
    platforms="ALL",
    packages=["beetsplug"],
    install_requires=[
        "beets>=1.6.0",
        "plexapi>=4.15.0",
        "pyyaml>=6"
    ],
    extras_require={
        "dev": [
            "musicbrainzngs>=0.7.0"
        ]
    },
    classifiers=[
        'Topic :: Multimedia :: Sound/Audio',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Programming Language :: Python :: 3'
    ]
)
