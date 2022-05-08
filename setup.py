import setuptools 
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
	name='garagepi',
	version='1.0.0',
	description='Driver for sending Thingspeak data',
	url='https://github.com/bbaumg/garagepi',
	author='bbaumg',
	license='MIT',
	packages=[''],
	install_requires=['smbus', 
    'RPi.GPIO', 'twilio']
)
