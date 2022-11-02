# SCT013 

import serial

class SCT013:

    import requests
    import time

    cacheTime = 10
    config = None
    configConfig = None
    configSCT013 = None
    consumedW = 0
    debugLevel = 0
    fetchFailed = False
    generatedW = 0
    importW = 0
    exportW = 0
    lastFetch = 0
    master = None
    status = False
    timeout = 10
    voltage = 0
    arduino=0
    arduinoIP=0
    threePhases=False
    consumption=False
    generation=False

    def __init__(self, master):
        self.master = master
        self.config = master.config
        try:
            self.configConfig = master.config["config"]
        except KeyError:
            self.configConfig = {}
        try:
            
            if self.configConfig.get("numberOfPhases",1)==3:
               self.threePhases = True

        except KeyError:
            self.threePhases = False
        try:
            self.configSCT013 = master.config["sources"]["SCT013"]
        except KeyError:
            self.configSCT013 = {}
        self.debugLevel = self.configConfig.get("debugLevel", 0)
        self.status = self.configSCT013.get("enabled", False)
        self.consumption = self.configSCT013.get("consumption", False)
        self.generation = self.configSCT013.get("generation", False)
        self.arduinoUSB = self.configSCT013.get("arduinoPort", None)
        self.arduinoIP = self.configSCT013.get("arduinoIP", None)

        # Unload if this module is disabled or misconfigured
        if (not self.status):
            self.master.releaseModule("lib.TWCManager.EMS", "SCT013")
            return None

        if self.arduinoUSB != None:
           self.arduino = serial.Serial(self.arduinoUSB,baudrate=9600, timeout = 3.0)

    def debugLog(self, minlevel, message):
        self.master.debugLog(minlevel, "SCT013", message)

    def getConsumption(self):

        if not self.status:
            self.debugLog(10, "SCT013 EMS Module Disabled. Skipping getConsumption")
            return 0

        # Perform updates if necessary
        self.update()

        # Return consumption value
        return float(self.consumedW)

    def getGeneration(self):

        if not self.status:
            self.debugLog(10, "SCT013 EMS Module Disabled. Skipping getGeneration")
            return 0

        # Perform updates if necessary
        self.update()

        # Return generation value
        if not self.generatedW:
            self.generatedW = 0
        return float(self.generatedW)


    def update(self):

        if (int(self.time.time()) - self.lastFetch) > self.cacheTime:
            # Cache has expired. Fetch values from SCT013.

            try:
                txt=''

                if self.arduinoUSB != None:
                   while self.arduino.inWaiting() > 0:
                      txt = str(self.arduino.readline())
                else:
                   url = "http://"+self.arduinoIP
                   r = self.requests.get(url, timeout=self.timeout)
                   r.raise_for_status()
                   txt = str(r.content)

                try:       
                   if self.consumption:
                      if txt.index("IrmsA0 = "):
                         txt2 = txt[txt.find("IrmsA0 = ")+9:txt.find(" EndA0")]
                         txt2 = txt2.replace(' ','')
                         if not txt2:
                            self.consumedW=0
                         elif self.threePhases:
                            # Three Phases convertAmps will return the watts * 3 
                            self.consumedW=self.master.convertAmpsToWatts(float(txt2))/3
                         else:
                            self.consumedW=self.master.convertAmpsToWatts(float(txt2))
                      if txt.index("IrmsA1 = ") and self.threePhases:
                         txt2 = txt[txt.find("IrmsA1 = ")+9:txt.find(" EndA1")]
                         txt2 = txt2.replace(' ','')
                         if txt2:
                            self.consumedW=self.consumedW+self.master.convertAmpsToWatts(float(txt2))/3
                      if txt.index("IrmsA2 = ") and self.threePhases:
                         txt2 = txt[txt.find("IrmsA2 = ")+9:txt.find(" EndA2")]
                         txt2 = txt2.replace(' ','')
                         if txt2:
                            self.consumedW=self.consumedW+self.master.convertAmpsToWatts(float(txt2))/3
                except:
                   self.master.debugLog(10, "SCT013","Phase consumption not found")
                   self.consumedW=self.consumedW

                try:
                   if self.generation:
                      if txt.index("IrmsA3 = "):
                         txt3 = txt[txt.find("IrmsA3 = ")+9:txt.find(" EndA3")]
                         txt3 = txt3.replace(' ','')
                         if not txt3:
                            self.generatedW=0
                         elif self.threePhases:
                            # Three Phases convertAmps will return the watts * 3 
                            self.generatedW=self.master.convertAmpsToWatts(float(txt3))/3
                         else:
                            self.generatedW=self.master.convertAmpsToWatts(float(txt3))
                      if txt.index("IrmsA4 = ") and self.threePhases:
                         txt3 = txt[txt.find("IrmsA4 = ")+9:txt.find(" EndA4")]
                         txt3 = txt3.replace(' ','')
                         if txt3:
                            self.generatedW=self.generatedW+self.master.convertAmpsToWatts(float(txt3))/3
                      if txt.index("IrmsA5 = ") and self.threePhases:
                         txt3 = txt[txt.find("IrmsA5 = ")+9:txt.find(" EndA5")]
                         txt3 = txt3.replace(' ','')
                         if txt3:
                            self.generatedW=self.generatedW+self.master.convertAmpsToWatts(float(txt3))/3
                except:
                   self.master.debugLog(10, "SCT013","Phase generation not found")
                   self.generatedW=self.generatedW

            except (KeyError, TypeError) as e:
                self.debugLog(
                4, "Exception during parsing Meter Data (Consumption)"
                )
                self.debugLog(10, e)

            # Update last fetch time
            if self.fetchFailed is not True:
                self.lastFetch = int(self.time.time())

            return True
        else:
            # Cache time has not elapsed since last fetch, serve from cache.
            return False
