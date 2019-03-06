import os, sys, time, json
sys.path.insert(0, r'/app/pyCli/')
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
from uuid import uuid4

print( "Enviùronment", os.environ)
try:
   os.environ["SELENIUM"] = "http://172.17.0.3:4444/wd/hub"
except KeyError:
   print ("Please set the environment variable SELENIUM to Selenium URL")
   sys.exit(1)

profiledir=os.path.join(".","firefox_cache")
if not os.path.exists(profiledir): os.makedirs(profiledir)
print("Conectando a wsp")
driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor=os.environ["SELENIUM"])


print('Pedira el qr')
name = uuid4().hex+'.png'
if os.path.exists(name): os.remove(name)
driver.get_qr(name)
print('Guarda el qr')
os.rename('./'+name,'/app/files/qr/'+name)


print("Waiting for QR")
driver.wait_for_login()


while True:
   time.sleep(30)
   driver.send_message_to_id("5215569388165@c.us","hola")
   print(" Bateria ",driver.get_battery_level())
   print(" Number ",driver.get_phone_number())
   print(" Status ",driver.get_status())
   name = uuid4().hex+'.png'
   if os.path.exists(name): os.remove(name)
   driver.screenshot(name)
   print('Guarda foto')
   os.rename('./'+name,'/app/files/qr/'+name)

# print("chats whit messages not read", driver.get_chats_whit_messages_not_read())

# for chat in driver.get_chats_whit_messages_not_read():
#    print(driver.get_all_messages_in_chat(chat[0]))
#    for message in driver.get_all_messages_in_chat(chat[0]):
#       print(message)
   




