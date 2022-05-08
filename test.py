import os
import RPi.GPIO as GPIO
import time
import logging
import yaml
from datetime import datetime
import twilio
import twilio.rest
from thingspeak.thingspeak import thingspeak
from bme280.bme280 import bme280

# packages needed:
#   sudo apt install python3-pip python3-virtualevn
#   pip install RPi.GPIO
#   pip install twilio
#   pip install both of mine from github


# Setup logging
#logLevel = logging.CRITICAL
#logLevel = logging.ERROR
#logLevel = logging.WARNING
#logLevel = logging.INFO
logLevel = logging.DEBUG
logFormat = '%(asctime)s - %(module)s %(funcName)s - %(levelname)s - %(message)s'
logDateFormat = '%Y-%m-%d %H:%M:%S'
logFilename = 'garagepi.log'
#logHandlers = [logging.FileHandler(logFilename)]
logHandlers = [logging.FileHandler(logFilename), logging.StreamHandler()]
logging.basicConfig(level = logLevel, format = logFormat, datefmt = logDateFormat, handlers = logHandlers)
logger = logging.getLogger(__name__)

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# END SETUP - BEGIN FUNCTIONS
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def sendSMS(message):
  logger.info("Starting...  Sending SMS Message:  '" + str(message) + "'")
  twilioClient = twilio.rest.Client(appSettings['TWILIO']['SID'], appSettings['TWILIO']['TOKEN'])
  message = twilioClient.messages.create(
    to = appSettings['TWILIO']['TO'], 
    from_= appSettings['TWILIO']['FROM'],
    body = message)
  logger.info("Complete...  Sending SMS Message")

def getDoorStatus(doorName):
  logger.info("Starting... Check the door status:  '" + str(doorName) + "'")
  if GPIO.input(appSettings[str(doorName)]['UPGPIO']) == False and GPIO.input(appSettings[str(doorName)]['DOWNPGPIO']) == False:
    logger.info("Door is opening/closing")
    doorState = "Moving"
    #openning/closing
  elif GPIO.input(appSettings[str(doorName)]['UPGPIO']) == False and GPIO.input(appSettings[str(doorName)]['DOWNPGPIO']) == True:
    logger.info("Door is closed")
    doorState = "Closed"
    #door is down
  elif GPIO.input(appSettings[str(doorName)]['UPGPIO']) == True and GPIO.input(appSettings[str(doorName)]['DOWNPGPIO']) == False:
    logger.info("Door is open")
    doorState = "Open"
    #door is up
  else:
    logger.error("Door is broken")
    doorState = "Error"
    #error
  logger.debug(doorState)
  return doorState


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# END FUNCTIONS - BEGIN PROGRAM
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
logger.critical("**************************************************")
logger.critical("*")
logger.critical("* Starting Program")
logger.critical("*")
logger.critical("**************************************************")
logger.critical(os.uname())
logger.critical(GPIO.RPI_INFO)
logger.critical("Log Level = " + str(logLevel))

logger.info("Reading config file")
with open("settings.yaml", 'r') as stream:
  appSettings=yaml.safe_load(stream)
  logger.info(appSettings)

logger.info("Setting up GPIO Inputs")
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)
GPIO.setup(appSettings['DOORMAIN']['UPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(appSettings['DOORMAIN']['DOWNPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(appSettings['DOORSIDE']['UPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(appSettings['DOORSIDE']['DOWNPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
# logger.info("GPIO inMainDoorUp(" + str(inMainDoorUp) + "): " + str(GPIO.input(inMainDoorUp)))
# logger.info("GPIO inMainDoorDown(" + str(inMainDoorDown) + "): " + str(GPIO.input(inMainDoorDown)))
# logger.info("GPIO inSideDoorUp(" + str(inSideDoorUp) + "): " + str(GPIO.input(inSideDoorUp)))
# logger.info("GPIO inSideDoorDown(" + str(inSideDoorDown) + "): " + str(GPIO.input(inSideDoorDown)))
# logger.info("GPIO inMainDoorUp(" + str(inMainDoorUp) + "): " + str(GPIO.input(inMainDoorUp)))
# logger.info("GPIO inMainDoorDown(" + str(inMainDoorDown) + "): " + str(GPIO.input(inMainDoorDown)))
# logger.info("GPIO inSideDoorUp(" + str(inSideDoorUp) + "): " + str(GPIO.input(inSideDoorUp)))
# logger.info("GPIO inSideDoorDown(" + str(inSideDoorDown) + "): " + str(GPIO.input(inSideDoorDown)))
logger.info("GPIO Setup Complete")

dictMainDoor = dict()
dictSideDoor = dict()
logger.debug(dictMainDoor)
logger.debug(dictSideDoor)

"""
Array structure
one for each door
  last state change, State, date time
    stateLastChange: [State: Up/Down/Moving/Error, When:datetime]
  last state, state, date time
    stateLastRead: [State: Up/Down/Moving/Error, When:datetime]
Array for tracking Temp
  tempLastChange: [Temp: tempValue, when:datetime]
  timeLast: [Error Type???  datetimestamp

Logic
  Doors
    If State == error & time between last and current alert is => value?
      send alert
      update last alert time
      log alert to file
    If current state == stateLastChange then check if moving
      if == moving
        check time between lastStateChange and current...  
        If > ? seconds then send SMS error
        log alert to file
    if current state <> stateLastChange
      log the state change
      write the change to thingspeak
    
  Temp
    if current temp <> lastTemp then 
      write update to thingspeak
      update lastTemp with current temp
  Alert





"""




sensor = bme280()
sensorData = dict()
sensorData = sensor.readBME280Data()
logger.debug(sensorData)
#print(sensor.readBME280ID())
#print(sensor.readBME280Data()['TempF'])


logger.info("Test write to thingspeak")
channel = thingspeak(channel=appSettings['THINGSPEAK']['CHANNELID'], apiKey=appSettings['THINGSPEAK']['APIKEY'])
channel.field[channel.field_name(name='Humidity')] = sensorData['TempF']
channel.field[channel.field_name(name='Temp')] = sensorData['TempF']
channel.post_update()

#sendSMS("Current datetime is: " + str(datetime.now()))




try:
  while True:
    dictMainDoor['stateLastRead']['State'] = getDoorStatus("DOORMAIN")
    logger.debug(dictMainDoor)
    logger.debug(getDoorStatus("DOORSIDE"))
    # logger.debug("GPIO inMainDoorUp(" + str(inMainDoorUp) + "): " + str(GPIO.input(inMainDoorUp)))
    # logger.debug("GPIO inMainDoorDown(" + str(inMainDoorDown) + "): " + str(GPIO.input(inMainDoorDown)))
    # logger.debug("GPIO inSideDoorUp(" + str(inSideDoorUp) + "): " + str(GPIO.input(inSideDoorUp)))
    # logger.debug("GPIO inSideDoorDown(" + str(inSideDoorDown) + "): " + str(GPIO.input(inSideDoorDown)))
    # time.sleep(1)

    time.sleep(3)
    
    

except KeyboardInterrupt:
    logger.critical("Keyboard Interrupt:  Program Exiting")
    GPIO.cleanup()
    #sendSMS("Program Ended")
    print(datetime.now().strftime("Program Shutdown -- %Y/%m/%d -- %H:%M  -- Goodbye! \n"))


