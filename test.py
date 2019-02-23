from socketIO_client_nexus import SocketIO, LoggingNamespace
from config import token
import os, sys, time, json
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import shutil
from uuid import uuid4

if os.path.exists('./firefox_cache_v2'): shutil.rmtree('./firefox_cache_v2')
profiledir=os.path.join(".","firefox_cache_v2")
if not os.path.exists(profiledir): os.makedirs(profiledir)
driver = None

def connectWsp():
    global driver
    if driver == None :
        driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor='http://172.17.0.3:4444/wd/hub')

def on_connect():
    print('connect')
    socketIO.emit("Auth",wsp)

def on_reconnect():
    print('reconnect')
    socketIO.emit("Auth",wsp)

def on_getQr(*args):
    global driver
    print('LLEGO')
    if driver != None:
        try:
            if driver.is_logged_in():
                print('Sesion ya iniciada')
            else:
                print('Pedira el qr')
                name = uuid4().hex+'.png'
                if os.path.exists(name): os.remove(name)
                driver.get_qr(name)
                print('Guarda el qr')
                os.rename('./'+name,'../files/qr/'+name)
                wsp['file'] = '/files/qr/'+name
                socketIO.emit('sendQr',{'idSend':args[0],'file':'/files/qr/'+name})
                print('Termino')
        except:
            wsp['success'] = 'no'
            wsp['data'] = 'errorGetQr'
            socketIO.emit('sendQr',wsp)

def on_welcome(*args):
    print('Nuevo agente')

# Conneción a SELENIUM #
print('Connectando')
#connectWsp()

# SOCKET CREDENTIALS #
socketIO = SocketIO("192.168.0.15",3000, LoggingNamespace)
wsp = { 'status':'desactiva','chats':None, 'token': token } 

# Auth #
socketIO.on('connect', on_connect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('etc', on_welcome)
socketIO.on('getQr',on_getQr)

socketIO.wait()