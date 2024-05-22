from setuptools import setup

setup(
    install_requires=["beets>=1.6.0", "plexapi>=4.15.0", "pyyaml>=6"],
    platforms="ALL",
    packages=["beetsplug.gdplaylists"],
)
