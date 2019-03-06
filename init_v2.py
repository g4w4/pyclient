# -*- coding: utf-8 -*-
from socketIO_client_nexus import SocketIO, LoggingNamespace
from config import token,ip,pathSource,selemiunIP
from Utils.logs import write_log
import os, sys, time, json
import shutil
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
    if driver.is_logged_in():
        write_log('Socket-Info','session started')
        socketIO.emit('sendQr',{'idSend':args[0],'status':'Session okay'})
    else:
        write_log('Socket-Info','go to qr')
        name = uuid4().hex+'.png'
        if os.path.exists(name): os.remove(name)
        driver.get_qr(name)
        write_log('Socket-Info','saving qr')
        shutil.move('./'+name,pathSource+name)
        socketIO.emit('sendQr',{'idSend':args[0],'file':str(pathSource+name)})
        on_waitLogin()


def on_waitLogin():
    global awaitLogin, driver,wsp
    if awaitLogin == None:
        awaitLogin = True
        driver.wait_for_login()
        wsp['status'] = 'active'
        wsp['numero'] = str(driver.get_phone_number())
        socketIO.emit('updateAcount',wsp)
        write_log('Socket-Info','session start')
        on_sendStatus()
        write_log('Socket-Info','session recovery')
        on_messagesOld()
        write_log('Socket-Info','session subscribe')
        driver.subscribe_new_messages(NewMessageObserver())
        


def on_screenShot(*args):
    global driver
    if driver != None:
        write_log('Socket-Info','go to screen')
        name = uuid4().hex+'.png'
        if os.path.exists(name): os.remove(name)
        driver.screenshot(name)
        write_log('Socket-Info','saving screen')
        shutil.move('./'+name,pathSource+name)
        socketIO.emit('sendScreen',{'idSend':args[0],'file':str(pathSource+name)})
    else :
        socketIO.emit('sendScreen',{'idSend':args[0],'status':'Error in connection'})    


def on_updateInfo(*args):
    global wsp
    print('updateInfo')
    wsp = args[0]


def on_closeSession():
    global awaitLogin, driver,wsp
    driver.unsubscribe_new_messages(NewMessageObserver())
    driver.close()
    awaitLogin = None
    driver = None
    wsp['status'] = 'desactiva'
    socketIO.emit('updateAcount',wsp)
    write_log('Socket-Info','session close')



def on_sendText():
    driver.send_message_to_id("5215569388165@c.us","hola es una prueba")


def on_sendStatus():
    time.sleep(5)
    if driver != None:
        socketIO.emit('sendStatus',{'batery':str(driver.get_battery_level()),'status':str(driver.get_status()),'phone':str(driver.get_phone_number())})


def on_messagesOld():
    time.sleep(10)
    write_log('Socket-Info','session despertar')
    for chat in driver.get_chats_whit_messages_not_read():
        write_log('Socket-Info','session iterar')
        for message in chat[1]:
            time.sleep(.5)
            socketIO.emit('newMessage',{'chat':chat[0],'message':message})


class NewMessageObserver:
    def on_message_received(self, new_messages):
        for message in new_messages:
            if message.type == 'chat':
                write_log('Socket-Info',"New message '{}' received from number {}".format(message.type, message.sender.id))
                socketIO.emit('newMessage',{'chat':message.sender.id,'message':message.content})
            else:
                write_log('Socket-Info',"New message of type '{}' received from number {}".format(message.type, message.sender.id))
                if message.type == 'image':
                    content =  str(message.save_media(pathSource,True))
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content,'type':'img','caption':message.caption})
                elif message.type == 'video':
                    content =  str(message.save_media(pathSource,True))
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content,'type':'video','caption':message.caption})
                elif message.type == 'document':
                    content =  str(message.save_media(pathSource,True))
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content,'type':'file','caption':message.caption})
                elif message.type == 'audio' or message.type == 'ptt':
                    content =  str(message.save_media(pathSource,True))
                    os.rename(pathSource+content, pathSource+content+'.ogg')
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content+'.ogg','type':'ogg','caption':message.caption})
                else:
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':'Contenido No soportado'})


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
socketIO.on('sendText',on_sendText)
socketIO.on('getStatus',on_sendStatus)

socketIO.wait()