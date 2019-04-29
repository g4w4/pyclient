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

################################################################
#       AFECTACIÓN EN OBTENER TODOS LOS CHAT SE OPTA           #
#       POR DESACTIVARLA HASTA QUE FUNCIONE NUEVAMENTE         #
#       FECHA DE DETECCION 2019-04-29                          #
################################################################

##### Setting for start ######
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
        global driver
        write_log('Socket-Info','Connection success')
        # In case of reconnect #
        if driver != None and driver.is_logged_in():
            # Send account info #
            _wsp = {}
            _wsp['whatsAppJoin'] = driver.is_logged_in()
            _wsp['bateryLevel'] = driver.get_battery_level()
            _wsp['numero'] = driver.get_phone_number()
            _wsp['accountDown'] = False
            socketIO.emit('change',_wsp)

            # Send messages old #
            #oldMessges = Thread(target=getOldMessages)
            #oldMessges.start()
        else:

            # Send inital data #
            _wsp = {}
            _wsp['whatsAppJoin'] = False
            _wsp['accountDown'] = False
            socketIO.emit('change',_wsp)

            driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor=selemiunIP)
            write_log('Socket-Info','Check if have cache')
            rember = Thread(target=rememberSession)
            rember.start()

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
        global driver
        if driver == None:
            driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor=selemiunIP)
        if driver.is_logged_in():
            write_log('Socket-Info','session started') 
            socketIO.emit('change',{'whatsAppJoin':True,'accountDown':False})
            socketIO.emit('sendQr', {'socketId':args[0],'error':'The session is started'} )
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
        global awaitLogin, driver
        if awaitLogin == None:
            awaitLogin = True
            driver.wait_for_login()

            # Save session #
            driver.save_firefox_profile()

            # Send change in account #
            _wsp = {}
            _wsp['whatsAppJoin'] = True
            _wsp['bateryLevel'] = driver.get_battery_level()
            _wsp['numero'] = driver.get_phone_number()
            _wsp['accountDown'] = False
            socketIO.emit('change',_wsp)
            
            # Send login success #
            socketIO.emit('receiverLogin',args[0])
            write_log('Socket-Info','session start')

            # Send the status of account in whatsApp # 
            write_log('Socket-Info','Init event loop')
            loop = Thread(target=loopStatus)
            loop.start()

            # Send all messages unread #
            #oldMessges = Thread(target=getOldMessages)
            #oldMessges.start()

            # Suscribe to observable #
            driver.subscribe_new_messages(NewMessageObserver())

    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())
        awaitLogin = False

# started loop whats send status account #
def loopStatus():
    try:
        global wsp
        while driver != None:
            time.sleep(60)
            write_log('Socket-Info','Send account info')
            if driver.is_logged_in():
                _wsp = {}
                _wsp['whatsAppJoin'] = driver.is_logged_in()
                _wsp['bateryLevel'] = driver.get_battery_level()
                _wsp['numero'] = driver.get_phone_number()
                _wsp['accountDown'] = False
                socketIO.emit('change',_wsp)
            else:
                _wsp = {}
                _wsp['whatsAppJoin'] = driver.is_logged_in()
                _wsp['bateryLevel'] = driver.get_battery_level()
                _wsp['numero'] = driver.get_phone_number()
                _wsp['accountDown'] = False
                socketIO.emit('change',_wsp)
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

# Get all chats not read in the account ONLY in start session #
def getOldMessages():
    try:
        chats = {}
        write_log('Socket-Info','Get oldMessage')
        for chat in driver.get_chats_whit_messages():
            if chat.get('isGroup') != True:
                driver.chat_load_earlier_messages(chat.get('id'))
                chats[str(chat.get('id'))] = []
                for message in driver.get_all_messages_in_chat(chat.get('id'),True):
                    chatId = message._js_obj.get('chat').get('id').get('_serialized')
                    sendByMy = True if driver.get_phone_number() == message.sender.id else False
                    body = {'chat':chatId,'message':'','type':False,'caption':False,'sendBy':sendByMy}
                    #### Se desactiva la opción de recuperar mensajes de media 
                    #### para evitar sobre carga al inicio de sesion
                    # if message.type == 'image':
                    #     body['message'] = str(message.save_media(pathSource,True))
                    #     body['type'] = 'image'
                    #     body['caption'] = message.caption
                    # elif message.type == 'video':
                    #     body['message'] = str(message.save_media(pathSource,True))
                    #     body['type'] = 'video'
                    #     body['caption'] = message.caption
                    # elif message.type == 'document':
                    #     body['message'] = str(message.save_media(pathSource,True))
                    #     body['type'] = 'file'
                    #     body['caption'] = message.caption
                    # elif message.type == 'audio' or message.type == 'ptt':
                    #     content =  str(message.save_media(pathSource,True))
                    #     os.rename(content, content+'.ogg')
                    #     body['message'] = content
                    #     body['type'] = 'ogg'
                    # el
                    if message.type == 'chat':
                        body['message'] = message.content
                    else :
                        body['message'] = 'No soportado'

                    chats[chatId].append(body)
            else:
                outGroup = Thread(target=exitGroup,args=(chat.get('id'),))
                outGroup.start()
        socketIO.emit('oldMessages',chats)
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

# Remember session #
def rememberSession():
    global driver
    try:

        driver.wait_for_login(40)

        if driver.is_logged_in():
            # Send account info #
            write_log('Socket-Info','Send account info')
            _wsp = {}
            _wsp['whatsAppJoin'] = driver.is_logged_in()
            _wsp['bateryLevel'] = driver.get_battery_level()
            _wsp['numero'] = driver.get_phone_number()
            _wsp['accountDown'] = False
            socketIO.emit('change',_wsp)

            # Send messages old # 
            #oldMessges = Thread(target=getOldMessages)
            #oldMessges.start()

            # Send the status of account in whatsApp # 
            write_log('Socket-Info','Init event loop')
            loop = Thread(target=loopStatus)
            loop.start()

            # Suscribe to observable #
            driver.subscribe_new_messages(NewMessageObserver())
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

def exitGroup(idChat):
    global driver
    try:
        write_log('Socket-Info','Exit group')
        driver.exit_group(idChat)
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

def on_sendText(*args):
    try:
        id = args[0][0]
        message = args[0][1]
        write_log('Socket-Error','Send Message')

        send = Thread(target=sendText,args=(id,message))
        send.start()
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

def sendText(id,message):
    try:
        driver.send_message_to_id(id,message)
        driver.mark_read(id)
        socketIO.emit('newMessage',{'chat':id,'message':message,'sendBy':'Agent'})
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        socketIO.emit('errorSendTxt',{'chat':id,'message':message,'sendBy':'Agent'})
        errorSend(traceback.format_exc())

def on_sendFile(*args):
    try:
        write_log('Socket-Error','Send File')
        id = args[0][0]
        caption = args[0][1]
        typeMessage = args[0][2]
        fileMessage = args[0][3]
        send = Thread(target=sendFile,args=(id,caption,typeMessage,fileMessage))
        send.start()
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        socketIO.emit('errorSendFile',{'chat':id,'message':caption,'sendBy':'Agent'})
        errorSend(traceback.format_exc())

def sendFile(id,caption,typeMessage,fileMessage):
    try:
        write_log('Socket-Error','Sending File')
        driver.send_media(pathSource+fileMessage,id,caption)
        driver.mark_read(id)
        write_log('Socket-Error','Send File end')
        socketIO.emit('newMessage',{'chat':id,'message':fileMessage,'type':typeMessage,'caption':caption,'sendBy':'Agent'})
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        socketIO.emit('errorSendFile',{'chat':id,'message':caption,'sendBy':'Agent'})
        errorSend(traceback.format_exc())

def on_deleteChat(*args):
    try:
        print(args[0])
        write_log('Socket-Error','Delete Chat'+str(args[0]))
        delChat = Thread(target=delete,args=(args[0],))
        delChat.start()
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())

def delete(id):
    try:
        write_log('Socket-Error','Delete Chat'+str(id))
        driver.delete_chat(str(id))
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

# Send screenShoot to admin in BK#
def on_giveScreen(*args):
    try:
        _screen = Thread(target=screen,args=(args[0],))
        _screen.start()
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())
        socketIO.emit('sendScreen', {'socketId':args[0],'error':traceback.format_exc()} )

def screen(id):
    try:
        if driver != None:
            write_log('Socket-Info','go to screen'+id)
            name = uuid4().hex+'.png'
            if os.path.exists(name): os.remove(name)
            driver.screenshot(name)
            write_log('Socket-Info','saving screen')
            shutil.move('./'+name,pathSource+name)
            socketIO.emit('sendScreen',{'socketId':id,'file':str(name)})
        else:
            socketIO.emit('sendScreen', {'socketId':id,'error':'Browser not connected'} )
    except Exception as e:
        write_log('Socket-Error',traceback.format_exc())
        errorSend(traceback.format_exc())
        socketIO.emit('sendScreen', {'socketId':id,'error':traceback.format_exc()} )

##########################
#       OBSERVABLE       #
##########################
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
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content,'type':'image','caption':message.caption})
                elif message.type == 'video':
                    content =  str(message.save_media(pathSource,True))
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content,'type':'video','caption':message.caption})
                elif message.type == 'document':
                    content =  str(message.save_media(pathSource,True))
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content,'type':'file','caption':message.caption})
                elif message.type == 'audio' or message.type == 'ptt':
                    content =  str(message.save_media(pathSource,True))
                    os.rename(content, content+'.ogg')
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':content+'.ogg','type':'ogg','caption':message.caption})
                else:
                    socketIO.emit('newMessage',{'chat':message.sender.id,'message':'Contenido No soportado'})


##### SOCKET LISSENER #####
socketIO.on('connect', on_connect)
socketIO.on('welcome', on_welcome)
socketIO.on('reconnect', on_reconnect)
socketIO.on('getQr',on_getQr)
socketIO.on('matchUpdate',on_matchUpdate)
socketIO.on('giveScreen',on_giveScreen)
socketIO.on('sendText',on_sendText)
socketIO.on('sendFile',on_sendFile)
socketIO.on('deleteChat',on_deleteChat)

socketIO.wait()


# def on_sendFile(*args):
#    try:
#         id = args[0][0]
#         caption = args[0][1]
#         typeMessage = args[0][2]
#         fileMessage = args[0][3]
#         send = Thread(target=sendFile,args=(id,caption,typeMessage,fileMessage))
#         send.start()
#     except Exception as e:
#         write_log('Socket-Error',traceback.format_exc())
#         socketIO.emit('errorSendFile',{'chat':id,'message':caption,'sendBy':'Agent'})
#         errorSend(traceback.format_exc())