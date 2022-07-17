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
logLevel = logging.CRITICAL
#logLevel = logging.ERROR
#logLevel = logging.WARNING
#logLevel = logging.INFO
#logLevel = logging.DEBUG
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
  logger.info("---------------------------------------Starting...  Sending SMS Message:  '" + str(message) + "'")
  twilioClient = twilio.rest.Client(appSettings['TWILIO']['SID'], appSettings['TWILIO']['TOKEN'])
  message = twilioClient.messages.create(
    to = appSettings['TWILIO']['TO'], 
    from_= appSettings['TWILIO']['FROM'],
    body = message)
  logger.info("Complete...  Sending SMS Message")

def getDoorStatus(doorName):
  logger.info("---------------------------------------Starting... Check the door status:  '" + str(doorName) + "'")
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

def setupDict(dictObj, dictName):
  #dictObj = dict()
  #dictObj['objectName'] = dictName.name
  #dictObj['name'] = dictName.name
  dictObj['name'] = dictName
  dictObj['lastStateChange'] = dict()
  dictObj['lastStateChange']['State'] = 'none'
  dictObj['lastStateChange']['When'] = 'none'
  dictObj['stateLastRead'] = dict()
  dictObj['stateLastRead']['State'] = 'none'
  dictObj['stateLastRead']['When'] = 'none'
  logger.debug(dictObj)


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

logger.critical("Reading config file")
with open("settings.yaml", 'r') as stream:
  appSettings=yaml.safe_load(stream)
  logger.info(appSettings)

logLevelNew = appSettings['LOGLEVEL']
logger.critical("Changing log level from " + str(logLevel) + " to " + str(logLevelNew))
logging.getLogger().setLevel(logLevelNew)

logger.info("Setting up GPIO Inputs")
GPIO.setmode(GPIO.BCM)
#GPIO.setwarnings(False)
GPIO.setup(appSettings['DOORMAIN']['UPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(appSettings['DOORMAIN']['DOWNPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(appSettings['DOORSIDE']['UPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(appSettings['DOORSIDE']['DOWNPGPIO'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
logger.info("GPIO Setup Complete")

logger.info("Setting up dictionary for tracking states of things")
dictMainDoor = dict()
setupDict(dictMainDoor, 'dictMainDoor')
logger.debug(dictMainDoor)
dictSideDoor = dict()
setupDict(dictSideDoor, 'dictSideDoor')
logger.debug(dictSideDoor)
dictTemp = dict()
setupDict(dictTemp, 'dictTemp')
logger.debug(dictTemp)
dictHumid = dict()
setupDict(dictHumid, 'dictHumid')
logger.debug(dictHumid)
dictPressure = dict()
setupDict(dictPressure, 'dictPressure')
logger.debug(dictPressure)
# dictAlert = dict()
# setupDict(dictAlert)
# logger.debug(dictAlert)


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




#sendSMS("Current datetime is: " + str(datetime.now()))




try:
  while True:
    logger.info("========================== Top of Main Loop ==========================")
    loopTime = datetime.now()
    logger.debug("Time = " + str(loopTime))
    anyChanges = False
    # Read the environmental sensor and store in a dictionaries for later use
    sensor = bme280()
    sensorData = dict()
    sensorData = sensor.readBME280Data()
    logger.debug(sensorData)

    # Prepare the thingspeak Channel
    channel = thingspeak(channel=appSettings['THINGSPEAK']['CHANNELID'], apiKey=appSettings['THINGSPEAK']['APIKEY'])

    # Test if the temp has changed
    logger.debug
    dictTemp['stateLastRead']['State'] = round(sensorData['TempF'], 0)
    dictTemp['stateLastRead']['When'] = loopTime
    if dictTemp['lastStateChange']['State'] == 'none' or dictTemp['lastStateChange']['State'] != dictTemp['stateLastRead']['State']:
      dictTemp['lastStateChange']['State'] = dictTemp['stateLastRead']['State']
      dictTemp['lastStateChange']['When'] = dictTemp['stateLastRead']['When']
      channel.field[channel.field_name(name='Temp')] = dictTemp['lastStateChange']['State']
      anyChanges = True
      logger.info("Temp has changed since last reading")
    else:
      logger.debug("Temp has NOT changed since last reading")
    logger.debug(dictTemp)

    # Test if the humidity has changed
    dictHumid['stateLastRead']['State'] = round(sensorData['Humidity'], 0)
    dictHumid['stateLastRead']['When'] = loopTime
    if dictHumid['lastStateChange']['State'] == 'none' or dictHumid['lastStateChange']['State'] != dictHumid['stateLastRead']['State']:
      dictHumid['lastStateChange']['State'] = dictHumid['stateLastRead']['State']
      dictHumid['lastStateChange']['When'] = dictHumid['stateLastRead']['When']
      channel.field[channel.field_name(name='Humidity')] = dictHumid['lastStateChange']['State']
      anyChanges = True
      logger.info("Humidity has changed since last reading")
    else:
      logger.debug("Humidity has NOT changed since last reading")
    logger.debug(dictHumid)

    # Test if the pressure has changed
    dictPressure['stateLastRead']['State'] = round(sensorData['Pressure'], 0)
    dictPressure['stateLastRead']['When'] = loopTime
    if dictPressure['lastStateChange']['State'] == 'none' or dictPressure['lastStateChange']['State'] != dictPressure['stateLastRead']['State']:
      dictPressure['lastStateChange']['State'] = dictPressure['stateLastRead']['State']
      dictPressure['lastStateChange']['When'] = dictPressure['stateLastRead']['When']
      channel.field[channel.field_name(name='Pressure')] = dictPressure['lastStateChange']['State']
      anyChanges = True
      logger.info("Pressure has changed since last reading")
    else:
      logger.debug("Pressure has NOT changed since last reading")
    logger.debug(dictPressure)
    
    # Test the state of the main door
    dictMainDoor['stateLastRead']['State'] = getDoorStatus("DOORMAIN")
    dictMainDoor['stateLastRead']['When'] = loopTime
    if dictMainDoor['lastStateChange']['State'] == 'none' or dictMainDoor['lastStateChange']['State'] != dictMainDoor['stateLastRead']['State']:
      dictMainDoor['lastStateChange']['State'] = dictMainDoor['stateLastRead']['State']
      dictMainDoor['lastStateChange']['When'] = dictMainDoor['stateLastRead']['When']
      channel.field[channel.field_name(name='MainDoor')] = dictMainDoor['lastStateChange']['State']
      anyChanges = True
      logger.info("Pressure has changed since last reading")
    else:
      logger.debug("Pressure has NOT changed since last reading")
    logger.debug(dictMainDoor)

    # Test if the state of the side door
    dictSideDoor['stateLastRead']['State'] = getDoorStatus("DOORSIDE")
    dictSideDoor['stateLastRead']['When'] = loopTime
    if dictSideDoor['lastStateChange']['State'] == 'none' or dictSideDoor['lastStateChange']['State'] != dictSideDoor['stateLastRead']['State']:
      dictSideDoor['lastStateChange']['State'] = dictSideDoor['stateLastRead']['State']
      dictSideDoor['lastStateChange']['When'] = dictSideDoor['stateLastRead']['When']
      channel.field[channel.field_name(name='MainDoor')] = dictSideDoor['lastStateChange']['State']
      anyChanges = True
      logger.info("Pressure has changed since last reading")
    else:
      logger.debug("Pressure has NOT changed since last reading")
    logger.debug(dictSideDoor)

    # Send the data to thingspeak
    if anyChanges == True:
      logger.info("Writing to Thingspeak")
      channel.post_update()
    else:
      logger.info("No Changes occured, not writing to thingspeak")


    logger.info("Pausing for a few seconds")
    time.sleep(10)
    
    

except KeyboardInterrupt:
    logger.critical("Keyboard Interrupt:  Program Exiting")
    GPIO.cleanup()
    #sendSMS("Program Ended")
    print(datetime.now().strftime("Program Shutdown -- %Y/%m/%d -- %H:%M  -- Goodbye! \n"))


