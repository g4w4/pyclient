import os, sys, time, json
sys.path.insert(0, r'/app/pyCli/')
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import traceback

print( "Environment", os.environ)
try:
   os.environ["SELENIUM"] = "http://172.22.0.2:4444/wd/hub"
except KeyError:
   print ("Please set the environment variable SELENIUM to Selenium URL")
   sys.exit(1)


profiledir=os.path.join(".","firefox_cache_v2")
if not os.path.exists(profiledir): os.makedirs(profiledir)
print("Conectando a selenium ")
driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor='172.18.0.2:4444/wd/hub')
print("Conecto y saco screen shot")
print("Espero login 30 seg")
driver.screenshot('shot.png')
try:
    driver.wait_for_login(30)
except Exception as e:
    print(traceback.format_exc())
if driver.is_logged_in():
    print("conectado a wsp")
    driver.screenshot('shot.png')
else:
    print("Waiting for QR")
    driver.get_qr('lala.png')
    print("Waiting for QR")
    driver.wait_for_login()
    print("Bot started")
    driver.save_firefox_profile()