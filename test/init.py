from socketIO_client_nexus import SocketIO, LoggingNamespace
from config import infoClient
import os, sys, time, json
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import shutil


socketIO = SocketIO('172.18.0.4',4000, LoggingNamespace)
wsp = {'status':'off','data':None,'token':infoClient['token']}

if os.path.exists('./firefox_cache_v2'): shutil.rmtree('./firefox_cache_v2')
profiledir=os.path.join(".","firefox_cache_v2")
if not os.path.exists(profiledir): os.makedirs(profiledir)
driver = WhatsAPIDriver(profile=profiledir, client='remote', command_executor=os.environ["SELENIUM"])


def on_connect():
    print('connect')
    socketIO.emit('status',wsp)

def on_welcome():
    print('Sesion completada')

def on_disconnect():
    print('Session desconectada')

def on_reconnect():
    print('reconnect')
    socketIO.emit('status',wsp)

def on_getQr():
    try:
        print('getQr')
        if driver.is_logged_in():
            wsp['success'] = 'no'
            wsp['data'] = 'sessionOn'
            socketIO.emit('sendQr',wsp)
        else:
            if os.path.exists('qr.png'): os.remove('qr.png')
            driver.get_qr('qr.png')
            wsp['success'] = 'yes'
            wsp['data'] = 'sendQr'
            socketIO.emit('sendQr',wsp)
            driver.wait_for_login()
            wsp['status'] = driver.is_logged_in() if 'on' else 'off'
            socketIO.emit("status",wsp)
    except:
        wsp['success'] = 'no'
        wsp['data'] = 'errorGetQr'
        socketIO.emit('sendQr',wsp)

def on_getStatus():
    try:
        wsp['success'] = 'yes'
        wsp['data'] = driver.is_logged_in() if 'sessionOn' else 'NotConnection'
        socketIO.emit('sendStatus',wsp)
    except:
        wsp['success'] = 'no'
        wsp['data'] = 'errorGetStatus'
        socketIO.emit('sendStatus',wsp)

def on_getChatList():
    print('on_getChatList')
    try:
        if driver.is_logged_in():
            contacts = []
            for ids in driver.get_all_chat_ids():
                con = driver.get_chat_from_id( str(ids) )
                contacts.append( {'ID':str(ids),"info":str(con)} )
            wsp['data'] = contacts
            wsp['success'] = 'ok'
            socketIO.emit('sendChatList',wsp)
        else:
            wsp['success'] = 'desc'
            socketIO.emit('sendChatList',wsp)
    except:
        wsp['success'] = 'errorGetChatList'
        socketIO.emit('sendChatList',wsp)

def on_sendMessage(*args):
    try:
        idChat = str(args[0]['idChat'])
        message = str(args[0]['message'])

        if driver.is_logged_in():
            send = False

            for ids in driver.get_all_chat_ids():
                if str(ids) == idChat:
                    send = True
                    try:
                        driver.chat_send_message(str(ids),message)
                    except:
                        wsp['success'] = 'errorSendMessage'
                        socketIO.emit('getStatusMessage',wsp)  

            if send :
                wsp['data'] = {'status':'success','desc':'Mensaje Enviado'}
            else :
                wsp['data'] = {'status':'error','desc':'Chat no existe'}

            wsp['success'] = 'ok'
            socketIO.emit('getStatusMessage',wsp)

        else:
            wsp['success'] = 'desc'
            socketIO.emit('getStatusMessage',wsp)

    except:
        wsp['success'] = 'errorSendMessage'
        socketIO.emit('getStatusMessage',wsp)

def on_sendMedia(*args):
    try:
        idChat = str(args[0]['idChat'])
        message = str(args[0]['message'])
        media = str(args[0]['file'])

        if driver.is_logged_in():
            send = False

            for ids in driver.get_all_chat_ids():
                if str(ids) == idChat:
                    send = True
                    try:
                        driver.send_media('../files/'+media,str(ids),message)
                    except:
                        wsp['success'] = 'errorSendMedia'
                        socketIO.emit('getStatusMedia',wsp)  

            if send :
                wsp['data'] = {'status':'success','desc':'Mensaje Enviado'}
            else :
                wsp['data'] = {'status':'error','desc':'Chat no existe'}

            wsp['success'] = 'ok'
            socketIO.emit('getStatusMedia',wsp)

        else:
            wsp['success'] = 'desc'
            socketIO.emit('getStatusMedia',wsp)

    except:
        wsp['success'] = 'errorSendMessage'
        socketIO.emit('getStatusMedia',wsp)

def on_getMessages():
    try:
        print("Piden mensajes")
        if driver.is_logged_in():

            messagesArray = []

            for contact in driver.get_unread():

                messagesArray.append({'id':contact.messages[0].sender.id,'messages':[]})

                for message in contact.messages:

                    messagesArray[-1]['messages'].append({
                        'timestamp':str(message.timestamp),
                        'type':str(message.type),
                        'content':''
                    })

                    print(message)

                    if message.type == 'chat':
                        messagesArray[-1]['messages'][-1]['content']  = str(message.content)
                    elif message.type == 'image' or message.type == 'video' or message.type == 'document':
                        messagesArray[-1]['messages'][-1]['content']  = str(message.save_media('../files/',True)).replace('../files/','')
                        messagesArray[-1]['messages'][-1]['caption']  = message.caption
                    elif message.type == 'audio' or message.type == 'ptt':
                        messagesArray[-1]['messages'][-1]['content']  = str(message.save_media('../files/',True)).replace('../files/','')
                        os.rename('../files/'+messagesArray[-1]['messages'][-1]['content'], '../files/'+messagesArray[-1]['messages'][-1]['content']+'.ogg')
                        messagesArray[-1]['messages'][-1]['content'] = messagesArray[-1]['messages'][-1]['content']+'.ogg'
                    else:
                        messagesArray[-1]['messages'][-1]['content'] = 'Contenido no soportado'

            wsp['data'] = {'status':'success', 'data' : messagesArray}
            wsp['success'] = 'ok'
            socketIO.emit('sendAllMessages',wsp)

        else:

            wsp['success'] = 'desc'
            socketIO.emit('sendAllMessages',wsp)
    except:
        wsp['success'] = 'errorGetMessages'
        socketIO.emit('sendAllMessages',wsp)

# Auth #
socketIO.on('connect', on_connect)
socketIO.on('welcome', on_welcome)
socketIO.on('disconnect', on_disconnect)
socketIO.on('reconnect', on_reconnect)

# Connection Driver #
socketIO.on('getQr', on_getQr)
socketIO.on('getStatus', on_getStatus)
socketIO.on('getChatList',on_getChatList)
socketIO.on('sendMessage',on_sendMessage)
socketIO.on('sendMedia',on_sendMedia)
socketIO.on('getMessages', on_getMessages)



# # Listen
# socketIO.on('aaa_response', on_aaa_response)
# socketIO.emit('aaa')
# socketIO.emit('aaa')
# socketIO.wait(seconds=1)

# # Stop listening
# socketIO.off('aaa_response')
# socketIO.emit('aaa')
# socketIO.wait(seconds=1)

# # Listen only once
# socketIO.once('aaa_response', on_aaa_response)
# socketIO.emit('aaa')  # Activate aaa_response
# socketIO.emit('aaa')  # Ignore
socketIO.wait()
