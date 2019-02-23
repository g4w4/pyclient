from socketIO_client_nexus import SocketIO, LoggingNamespace
from config import token,ip,pathSource,selemiunIP
from Utils.logs import write_log
import os, sys, time, json
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import shutil
from uuid import uuid4

###### Setting for start ######
if os.path.exists('./firefox_cache_v2'): shutil.rmtree('./firefox_cache_v2')
profiledir=os.path.join(".","firefox_cache_v2")
if not os.path.exists(profiledir): os.makedirs(profiledir)
driver = None
awaitLogin = None

##### Function socket login #####
def on_connect():
    global awaitLogin, driver,wsp
    write_log('Socket-Info','Connection successfuly whit server')
    try:
        wsp['status'] =driver.is_logged_in() if 'active' else 'desactiva'
        socketIO.emit("Auth",wsp)
    except :
        socketIO.emit("Auth",wsp)


def on_reconnect():
    global awaitLogin, driver,wsp
    write_log('Socket-Info','Reconnect whit server')
    socketIO.emit("Auth",wsp)


def on_welcome():
    global driver,wsp
    write_log('Socket-Info','Server login success')
    if driver != None:
        wsp['status'] = 'active'
        socketIO.emit('updateAcount',wsp)


##### Function socket WAPI #####
def on_getQr(*args):
    write_log('Socket-Info','give the qr')
    global driver
    if driver == None:
        driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor=selemiunIP)
    try:
        if driver.is_logged_in():
             write_log('Socket-Info','session started')
             socketIO.emit('sendQr',{'idSend':args[0],'status':'Session okay'})
        else:
            write_log('Socket-Info','go to qr')
            name = uuid4().hex+'.png'
            if os.path.exists(name): os.remove(name)
            driver.get_qr(name)
            write_log('Socket-Info','saving qr')
            os.rename('./'+name,pathSource+name)
            socketIO.emit('sendQr',{'idSend':args[0],'file':str(pathSource+name)})
            on_waitLogin()
    except:
        socketIO.emit('sendQr',{'idSend':args[0],'status':'Error in connection'})


def on_waitLogin():
    global awaitLogin, driver,wsp
    if awaitLogin == None:
        awaitLogin = True
        driver.wait_for_login()
        wsp['status'] = 'active'
        socketIO.emit('updateAcount',wsp)
        write_log('Socket-Info','session start')
        driver.subscribe_new_messages(NewMessageObserver())


def on_screenShot(*args):
    global driver
    if driver != None:
        write_log('Socket-Info','go to screen')
        name = uuid4().hex+'.png'
        if os.path.exists(name): os.remove(name)
        driver.screenshot(name)
        write_log('Socket-Info','saving screen')
        os.rename('./'+name,pathSource+name)
        socketIO.emit('sendScreen',{'idSend':args[0],'file':str(pathSource+name)})
    else :
        socketIO.emit('sendScreen',{'idSend':args[0],'status':'Error in connection'})    


def on_updateInfo(*args):
    global wsp
    print('updateInfo')
    wsp = args[0]

def on_closeSession():
    global awaitLogin, driver,wsp
    driver.close()
    awaitLogin = None
    driver = None
    wsp['status'] = 'desactiva'
    socketIO.emit('updateAcount',wsp)
    write_log('Socket-Info','session close')


class NewMessageObserver:
    def on_message_received(self, new_messages):
        for message in new_messages:
            if message.type == 'chat':
                write_log('Socket-Info',"New message '{}' received from number {}".format(message.content, message.sender.id))
                socketIO.emit('newMessage',{'chat':message.sender.id,'message':message.content})
            else:
                write_log('Socket-Info',"New message of type '{}' received from number {}".format(message.type, message.sender.id))


##### SOCKET CREDENTIALS #####
write_log('Socket-Info','Connect whit server')
socketIO = SocketIO(ip,3000, LoggingNamespace)
wsp = { 'status':'desactiva','chats': None, 'token': token } 

##### SOCKET LISSENER #####
socketIO.on('connect', on_connect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('welcome', on_welcome)
socketIO.on('getQr',on_getQr)
socketIO.on('getScreenShot',on_screenShot)
socketIO.on('updateInfo',on_updateInfo)
socketIO.on('closeSession',on_closeSession)

socketIO.wait()