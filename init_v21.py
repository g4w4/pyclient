from socketIO_client_nexus import SocketIO, LoggingNamespace
from config import token,ip,pathSource,selemiunIP
from Utils.logs import write_log
import os, sys, time, json
import shutil
import traceback
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import shutil
from uuid import uuid4
from threading import Thread

##### Setting for start ######
if os.path.exists('./firefox_cache_v2'): shutil.rmtree('./firefox_cache_v2')
profiledir=os.path.join(".","firefox_cache_v2")
if not os.path.exists(profiledir): os.makedirs(profiledir)

socketIO = SocketIO(ip,3000, LoggingNamespace)
wsp = None
driver = None
awaitLogin = None

# Functions Auth #
def on_connect(*args):
    write_log('Socket-Info','Connection whit server')
    socketIO.emit('Auth',token)

def on_welcome(*args):
    global wsp
    write_log('Socket-Info','Connection success')
    thread = Thread(target = loopStatus)
    thread.start()
    if wsp != None:
        old_Wsp = args[0]
        old_Wsp['numero'] =  wsp['numero']
        old_Wsp['chats'] = wsp['chats']
        socketIO.emit('updateAccount',old_Wsp)
    else:
        wsp = args[0]

def on_disconnect(*args):
    write_log('Socket-Info','Connection end')

def on_reconnect(*args):
    write_log('Socket-Info','Connection reconnect')
    socketIO.emit('Auth',token)

# Fuctions WhatsApp #
def on_getQr(*args):
    try:
        global driver,wsp
        if driver == None:
            driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor=selemiunIP)
        if driver.is_logged_in():
            write_log('Socket-Info','session started') 
            wsp['whatsAppJoin']  = True
            socketIO.emit('updateAccount',wsp)
        else:
            write_log('Socket-Info','go to qr')
            name = uuid4().hex+'.png'
            if os.path.exists(name): os.remove(name)
            driver.get_qr(name)
            write_log('Socket-Info','saving qr')
            shutil.move('./'+name,pathSource+name)
            write_log('Socket-Info','saving qr')
            socketIO.emit('sendQr',{'socketId':args[0],'file':str(name)})
            write_log('Socket-Info','saving qr')
            on_waitLogin(args[0])
    except Exception as e:
        socketIO.emit('sendQr', {'socketId':args[0],'error':traceback.format_exc()} )
        

def on_waitLogin(*args):
    global awaitLogin, driver,wsp
    if awaitLogin == None:
        awaitLogin = True
        driver.wait_for_login()
        wsp['whatsAppJoin'] = True
        socketIO.emit('updateAccount',wsp)
        socketIO.emit('receiverLogin',args[0])
        write_log('Socket-Info','session start')
        #driver.subscribe_new_messages(NewMessageObserver())


def on_test(*args):
    print("Consegui llegar")
    print(args)

def loopStatus():
    while driver != None:
        status = driver.
        time.sleep(2)

##### SOCKET LISSENER #####
socketIO.on('connect', on_connect)
socketIO.on('welcome', on_welcome)
socketIO.on('reconnect', on_reconnect)
socketIO.on('getQr',on_getQr)
socketIO.on('Test',on_test)

socketIO.wait()