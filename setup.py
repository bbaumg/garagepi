import setuptools 
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
	name='garagepi',
	version='1.0.2',
	description='Driver for sending Thingspeak data',
	url='https://github.com/bbaumg/garagepi',
	author='bbaumg',
	license='MIT',
	install_requires=['smbus', 
    'RPi.GPIO', 'twilio', 'pyyaml', 'bme280==1.0.2', 'thingspeak==1.1.1'],
  dependency_links=['https://github.com/bbaumg/Python_BME280/tarball/master#egg=bme280-1.0.2',
    'https://github.com/bbaumg/Python_Thingspeak'
  ]
)
