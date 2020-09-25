
from setuptools import setup, find_packages
from angiogen.core.version import get_version

VERSION = get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='angiogen',
    version=VERSION,
    description='AngioGen allows the rapid and flexible generation of synthetic angiographic images for use in research and development.',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Jonny Jackson',
    author_email='jonny@jxn.ai',
    url='https://github.com/jnyjxn/angiogenapp',
    license='GNU GPLv3',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'angiogen': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        angiogen = angiogen.main:main
    """,
)
