from datetime import datetime
import time

startTime = datetime.now()

while True:
  loopTime = datetime.now()
  time.sleep(20)
  print(loopTime - startTime)

