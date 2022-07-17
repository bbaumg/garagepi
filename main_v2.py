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
  logger.info("----- Starting sendSMS ----------------------------------------------")
  logger.info("Sending SMS Message:  '" + str(message) + "'")
  twilioClient = twilio.rest.Client(appSettings['TWILIO']['SID'], appSettings['TWILIO']['TOKEN'])
  if not appSettings['TWILIO']['PAUSE']:
    message = twilioClient.messages.create(
      to = appSettings['TWILIO']['TO'], 
      from_= appSettings['TWILIO']['FROM'],
      body = message)
    logger.info("Complete...  Sending SMS Message")
  else:
    logger.info("In SMS Testing Mode...  No SMS Message Sent")
    logger.info("Symulated SMS Message:"
      + "\n\t\t\t\t\tto:\t" + str(appSettings['TWILIO']['TO'])
      + "\n\t\t\t\t\tfrom:\t" + str(appSettings['TWILIO']['FROM'])
      + "\n\t\t\t\t\tbody:\t" + message)

def getDoorStatus(doorName):
  logger.info("----- Starting getDoorStatus ----------------------------------------------")
  logger.debug('doorName = ' + str(doorName))
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

def setupDict(dictObj, dictionaryName, sensorDescription, alarmType):
  logger.info("----- Starting setupDict ----------------------------------------------")
  logger.debug('dictObj = ' + str(dictObj))
  logger.debug('dictionaryName = ' + str(dictionaryName))
  logger.debug('sensorDescription = ' + str(sensorDescription))
  dictObj['name'] = dictionaryName
  dictObj['description'] = sensorDescription
  dictObj['lastStateChange'] = dict()
  dictObj['lastStateChange']['State'] = 'none'
  dictObj['lastStateChange']['When'] = 'none'
  dictObj['lastStateChange']['Minutes'] = 0
  dictObj['stateLastRead'] = dict()
  dictObj['stateLastRead']['State'] = 'none'
  dictObj['stateLastRead']['When'] = 'none'
  dictObj['inAlarm'] = dict()
  dictObj['inAlarm']['State'] = False
  dictObj['inAlarm']['Type'] = alarmType
  dictObj['inAlarm']['When'] = 'none'
  dictObj['inAlarm']['Minutes'] = 0
  dictObj['alerted'] = dict()
  dictObj['alerted']['State'] = False
  dictObj['alerted']['When'] = 'none'
  dictObj['alerted']['Minutes'] = 0
  dictObj['alerted']['Count'] = 0
  logger.debug(dictObj)

def updateValues(dictObj, reading, loopTime, readingType):
  logger.info("----- Starting updateValues ----------------------------------------------")
  logger.debug('dictObj = ' + str(dictObj))
  logger.debug('reading = ' + str(reading))
  logger.debug('loopTime = ' + str(loopTime))
  logger.debug('readingType = ' + str(readingType))
  global anyChanges 
  global channel
  dictObj['stateLastRead']['State'] = reading
  dictObj['stateLastRead']['When'] = loopTime
  if dictObj['lastStateChange']['State'] == 'none' or dictObj['lastStateChange']['State'] != dictObj['stateLastRead']['State']:
    dictObj['lastStateChange']['State'] = dictObj['stateLastRead']['State']
    dictObj['lastStateChange']['When'] = dictObj['stateLastRead']['When']
    channel.field[channel.field_name(name=readingType)] = dictObj['lastStateChange']['State']
    anyChanges = True
    logger.info(str(readingType) + " has changed since last reading")
  else:
    dictObj['lastStateChange']['Minutes'] = (dictObj['stateLastRead']['When']-dictObj['lastStateChange']['When']).seconds #chang this to real minutes
    logger.info(str(readingType) + "  has NOT changed since last reading")
  logger.debug('anyChanges = ' + str(anyChanges))
  logger.debug(dictObj)

def testAlarm_old(dictObj, alarmType):
  logger.info("----- Starting testAlarm ----------------------------------------------")
  logger.debug('dictObj = ' + str(dictObj))
  logger.debug('alarmType = ' + str(alarmType))
  inAlarm = False
  #reAlarm = appSettings['ALARMS']['RETRY']
  reAlarm = 21
  alarmMessage = ''
  if(alarmType == 'Door'):
    if(dictObj['lastStateChange']['State'] != 'Closed' and dictObj['lastStateChange']['Minutes'] >= appSettings['ALARMS']['DOORTIME']):
      inAlarm = True
      alarmMessage = ("ALERT: The " + str(dictObj['description'])
      + " has been open for "
      + str(dictObj['lastStateChange']['Minutes'])
      + " minutes")
      logger.info(alarmMessage)
  elif(alarmType == 'Temp'):
    if(dictObj['lastStateChange']['State'] <= appSettings['ALARMS']['TEMPMIN']):
      #and dictObj['lastStateChange']['Minutes'] >= appSettings['ALARMS']['TEMPTIME']
      inAlarm = True
      alarmMessage = ("ALERT: The " + str(dictObj['description'])
      + " has been at "
      + str(dictObj['lastStateChange']['State'])
      + " degrees and has been below the minimum temp for "
      + str(dictObj['lastStateChange']['Minutes'])
      + " minutes")
      logger.info(alarmMessage)
    elif(dictObj['lastStateChange']['State'] >= appSettings['ALARMS']['TEMPMAX']):
      # and dictObj['lastStateChange']['Minutes'] >= appSettings['ALARMS']['TEMPTIME']
      inAlarm = True
      alarmMessage = ("ALERT: The " + str(dictObj['description'])
      + " has been at "
      + str(dictObj['lastStateChange']['State'])
      + " degrees and has been above the maximum temp for "
      + str(dictObj['lastStateChange']['Minutes'])
      + " minutes")
      logger.info(alarmMessage)
  else:
    inAlarm = True
    logger.warning("Some other alarm type was presented that is not handled")
  #logger.debug(dictObj['lastStateChange']['Minutes'])

  if(inAlarm == True):
    logger.info("Checking if an alert should be sent")
    if (dictObj['inAlarm']['State'] == True):
      logger.info("Alert has already been sent checking if a re-alert should be sent")
      dictObj['inAlarm']['Minutes'] = (dictObj['stateLastRead']['When']-dictObj['inAlarm']['When']).seconds #chang this to real minutes
      logger.info('Time since last alert = ' + str(dictObj['inAlarm']['Minutes']))
      if (dictObj['inAlarm']['Minutes'] >= reAlarm):
        logger.info("In alarm too long resending alert")
        sendSMS(alarmMessage)
        dictObj['inAlarm']['State'] = True
        dictObj['inAlarm']['When'] = loopTime
        dictObj['inAlarm']['Count'] += 1
      else:
        logger.info("already sent alarm not ready to resend")
    else:
      logger.info("Sending 1st alert")
      sendSMS(alarmMessage)
      dictObj['inAlarm']['State'] = True
      dictObj['inAlarm']['When'] = loopTime
      dictObj['inAlarm']['Count'] += 1
  else:
    logger.info("No alarms to alert on")
    logger.debug(dictObj)

def testAlarm(dictObj):
  logger.info("----- Starting testAlarm ----------------------------------------------")
  logger.debug('dictObj = ' + str(dictObj))
  alarmMessage = ''
  if(dictObj['inAlarm']['Type'] == 'Door'):
    logger.info("Testing Door alarm state")
    if(dictObj['lastStateChange']['State'] != 'Closed'):
      logger.debug("Door is NOT closed")
      updateAlarmState(dictObj, True)
      if(dictObj['inAlarm']['Minutes'] >= appSettings['ALARMS']['DOORTIME']):
        logger.info("Past the time in alarm threshold")
        #if(dictObj['alerted']['State'] == False):
        #  logger.info("Sending the first alert for this alarm")
        #  dictObj['alerted']['State'] = True
        #  dictObj['alerted']['When'] = loopTime
        #  dictObj['alerted']['Count'] += 1
        #  #sendSMS
        #elif(dictObj['alerted']['State'] == True and dictObj['stateLastRead']['When']-dictObj['alerted']['When'] >= appSettings['ALARMS']['RETRY']):
        #  logger.info("Sending repate alert for this alarm")
        #  dictObj['alerted']['Count'] += 1
        #  logger.info("Alert Count = " + str(dictObj['alerted']['Count']))
        #  #sendSMS
        #elif(dictObj['alerted']['State'] == True and dictObj['stateLastRead']['When']-dictObj['alerted']['When'] <= appSettings['ALARMS']['RETRY']):
        #  #do nothing
        #  logger.info("It has not been long enough to send a repeat alert")
        #else:
        #  logger.info("check logic for when to send the alert")
      else:
        logger.info("Not enough time has passed yet")
        #do something else
    else:
      logger.debug("Door is closed")
      updateAlarmState(dictObj, False)
  elif(dictObj['inAlarm']['Type'] == 'Temp'):
    logger.debug("Testing Temp alarm state")
    if(dictObj['lastStateChange']['State'] <= appSettings['ALARMS']['TEMPMIN'] or dictObj['lastStateChange']['State'] >= appSettings['ALARMS']['TEMPMAX']):
      logger.debug("Temp is outside accepted range")
      updateAlarmState(dictObj, True)
      if((dictObj['stateLastRead']['When']-dictObj['inAlarm']['When']).seconds >= appSettings['ALARMS']['TEMPTIME']):
        logger.info("Past the time in alarm threshold")
        #DO SOMETHING
      else:
        logger.info("Not enough time has passed yet")
        #do something else
    else:
      logger.debug("Temp is in an acceptable range")
      updateAlarmState(dictObj, False)
  else:
    logger.warning("Some other alarm type was presented that is not handled")
  logger.debug(dictObj)

def updateAlarmState(dictObj, alarmState):
  logger.info("----- Starting updateAlarmState ----------------------------------------------")
  logger.debug('dictObj = ' + str(dictObj))
  logger.debug('alarmState = ' + str(alarmState))
  if(alarmState == True):
    logger.info("In an alarmed state")
    dictObj['inAlarm']['State'] = True
    if(dictObj['inAlarm']['When'] == 'none'):
      dictObj['inAlarm']['When'] = loopTime
    dictObj['inAlarm']['Minutes'] = (dictObj['stateLastRead']['When']-dictObj['inAlarm']['When']).seconds
    logger.debug((dictObj['stateLastRead']['When']-dictObj['inAlarm']['When']).seconds)
  elif(alarmState == False):
    logger.info("NOT in an alarmed state")
    dictObj['inAlarm']['State'] = False
    dictObj['inAlarm']['When'] = 'none'
    dictObj['inAlarm']['Minutes'] = 0
  logger.debug(dictObj)

def testAlert(dictObj):
  logger.info("----- Starting testAlert ----------------------------------------------")
  logger.debug('dictObj = ' + str(dictObj))

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
setupDict(dictMainDoor, 'dictMainDoor', 'Main Garage Door', 'Door')
dictSideDoor = dict()
setupDict(dictSideDoor, 'dictSideDoor', 'Side Garage Door', 'Door')
dictTemp = dict()
setupDict(dictTemp, 'dictTemp', 'Garage Temperature', 'Temp')
dictHumid = dict()
setupDict(dictHumid, 'dictHumid', 'Garage Humidity', 'none')
dictPressure = dict()
setupDict(dictPressure, 'dictPressure', 'Garage Pressure', 'none')

try:
  while True:
    logger.info("================================ Top of Loop ================================")
    loopTime = datetime.now()
    alertMessage = ''
    anyChanges = False

    # Read the environmental sensor and store in a dictionaries for later use
    sensor = bme280()
    sensorData = dict()
    sensorData = sensor.readBME280Data()
    logger.debug(sensorData)

    # Prepare the thingspeak Channel
    channel = thingspeak(channel=appSettings['THINGSPEAK']['CHANNELID'], apiKey=appSettings['THINGSPEAK']['APIKEY'])

    # Take all of the readings and update the dictionaries and/or thingspeak channel.
    updateValues(dictTemp, round(sensorData['TempF'], 0), loopTime, 'Temp')
    updateValues(dictHumid, round(sensorData['Humidity'], 0), loopTime, 'Humidity')
    updateValues(dictPressure, round(sensorData['Pressure'], 0), loopTime, 'Pressure')
    updateValues(dictMainDoor, getDoorStatus("DOORMAIN"), loopTime, 'DoorMain')
    updateValues(dictSideDoor, getDoorStatus("DOORSIDE"), loopTime, 'DoorSide')
    
    # Send the data to thingspeak
    if anyChanges == True:
      logger.info("Writing to Thingspeak")
      channel.post_update()
    else:
      logger.info("No Changes occured, not writing to thingspeak")

    logger.debug('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
    testAlarm(dictMainDoor)
    testAlarm(dictSideDoor)
    testAlarm(dictTemp)

    logger.info("Pausing for a few seconds")
    time.sleep(20)
    
except KeyboardInterrupt:
  logger.critical("Keyboard Interrupt:  Program Exiting")
  print(datetime.now().strftime("Program Shutdown -- %Y/%m/%d -- %H:%M  -- Goodbye! \n"))
finally:
  logger.critical("!!!!!!!!!!!!!!!!!!!!!!!!! Exiting Program !!!!!!!!!!!!!!!!!!!!!!!!!")
  GPIO.cleanup()
  logger.critical("Program Ending = " + os.uname().nodename + ":" + __file__)
  sendSMS("Program Ended = " + os.uname().nodename + ":" + __file__)
  logger.critical("!!!!!!!!!!!!!!!!!!!!!!!!! End Program !!!!!!!!!!!!!!!!!!!!!!!!!")


