from socketIO_client_nexus import SocketIO, LoggingNamespace
#from config import infoClient
import os, sys, time, json
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import shutil


socketIO = SocketIO("192.168.0.15",3000, LoggingNamespace)
wsp = { 'status':'discconect','chats':None } 

def on_connect():
    print('connect')
    socketIO.emit("statusAcount",wsp)

def on_reconnect():
    print('reconnect')
    socketIO.emit("statusAcount",wsp)

def on_welcome():
    print('Sesion completada')

# Auth #
socketIO.on('connect', on_connect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('welcome', on_welcome)

socketIO.wait()