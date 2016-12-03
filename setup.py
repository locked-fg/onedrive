from setuptools import setup

setup(
   name='my_onedrive',
   version='0.1',
   description='My personal OneDrive API',
   author='Franz',
   author_email='code@locked.de',
   packages=['my_onedrive'],  #same as name
   install_requires=['requests']
)