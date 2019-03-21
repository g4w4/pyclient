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

#####################################
#          Functions Auth           #
#####################################
def on_connect(*args):
    write_log('Socket-Info','Connection whit server')
    socketIO.emit('Auth',token)

def on_welcome(*args):
    try:
        global wsp
        write_log('Socket-Info','Connection success')
        if wsp != None:
            old_Wsp = args[0]
            old_Wsp['numero'] =  wsp['numero']
            old_Wsp['chats'] = wsp['chats']
            socketIO.emit('updateAccount',old_Wsp)
            if driver.is_logged_in():
                oldMessges = Thread(target=getOldMessages)
                oldMessges.start()
        else:
            wsp = args[0]
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

def on_disconnect(*args):
    write_log('Socket-Info','Connection end')

def on_reconnect(*args):
    write_log('Socket-Info','Connection reconnect')
    socketIO.emit('Auth',token)


#####################################
#       Fuctions WhatsApp           #
#####################################

# Get the codeQr and emit the id Name #
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
            write_log('Socket-Info','send qr')
            socketIO.emit('sendQr',{'socketId':args[0],'file':str(name)})
            on_waitLogin(args[0])
    except Exception as e:
        socketIO.emit('sendQr', {'socketId':args[0],'error':traceback.format_exc()} )
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())
        
# await for login in whatsApp #
def on_waitLogin(*args):
    try:
        global awaitLogin, driver,wsp
        if awaitLogin == None:
            awaitLogin = True
            driver.wait_for_login()
            wsp['whatsAppJoin'] = True
            wsp['bateryLevel'] = driver.get_battery_level()
            wsp['numero'] = driver.get_phone_number()
            socketIO.emit('updateAccount',wsp)
            socketIO.emit('receiverLogin',args[0])
            write_log('Socket-Info','session start')

            # Send the status of account in whatsApp # 
            write_log('Socket-Info','Init event loop')
            loop = Thread(target=loopStatus)
            loop.start()

            # Send all messages unread #
            oldMessges = Thread(target=getOldMessages)
            oldMessges.start()

    except expression as identifier:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

# started loop whats send status account #
def loopStatus():
    try:
        global wsp
        while driver != None:
            time.sleep(60)
            if driver.is_logged_in():
                write_log('Socket-Info','Send account info')
                bateryLevel = driver.get_battery_level()
                numero = driver.get_phone_number()
                login = driver.is_logged_in()    
                socketIO.emit('statusAccount',[bateryLevel,numero,True])
            else:
                socketIO.emit('statusAccount',[wsp['bateryLevel'],wsp['numero'],False])
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

# Get all chats not read in the account ONLY in start session #
def getOldMessages():
    try:
        chats = {}
        write_log('Socket-Info','Get oldMessage')
        for chat in driver.get_chats_whit_messages_not_read():
            if chat.get('isGroup') != True:
                driver.chat_load_earlier_messages(chat.get('id'))
                chats[str(chat.get('id'))] = []
                for message in driver.get_all_messages_in_chat(chat.get('id'),True):
                    chatId = message._js_obj.get('chat').get('id').get('_serialized')
                    sendByMy = True if driver.get_phone_number() == message.sender.id else False
                    body = {'chat':chatId,'message':'','type':False,'caption':False,'sendBy':sendByMy}
                    if message.type == 'image':
                        body['message'] = str(message.save_media(pathSource,True))
                        body['type'] = 'img'
                        body['caption'] = message.caption
                    elif message.type == 'video':
                        body['message'] = str(message.save_media(pathSource,True))
                        body['type'] = 'video'
                        body['caption'] = message.caption
                    elif message.type == 'document':
                        body['message'] = str(message.save_media(pathSource,True))
                        body['type'] = 'file'
                        body['caption'] = message.caption
                    elif message.type == 'audio' or message.type == 'ptt':
                        content =  str(message.save_media(pathSource,True))
                        os.rename(content, content+'.ogg')
                        body['message'] = content
                        body['type'] = 'file'
                    elif message.type == 'chat':
                        body['message'] = message.content
                    else :
                        body['message'] = 'No soportado'

                    chats[chatId].append(body)
        socketIO.emit('oldMessages',chats)
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())


#####################################
#          Chat Functions           #
#####################################

# Receive info for the account is change #
def on_matchUpdate(*args):
    try:
        global wsp
        wsp = args[0]
        print(wsp)
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())


#####################################
#          Admin Functions          #
#####################################

# Send error to serverSocket 
def errorSend(error):
    socketIO.emit('clientError',[wsp['token'],error])

##### SOCKET LISSENER #####
socketIO.on('connect', on_connect)
socketIO.on('welcome', on_welcome)
socketIO.on('reconnect', on_reconnect)
socketIO.on('getQr',on_getQr)
socketIO.on('matchUpdate',on_matchUpdate)

socketIO.wait()