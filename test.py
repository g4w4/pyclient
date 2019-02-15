from socketIO_client_nexus import SocketIO, LoggingNamespace
from config import token
import os, sys, time, json
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import shutil


socketIO = SocketIO("192.168.40.15",3000, LoggingNamespace)
wsp = { 'status':'desactiva','chats':None, 'token': token } 

def on_connect():
    print('connect')
    socketIO.emit("addAccount",wsp)

def on_reconnect():
    print('reconnect')
    socketIO.emit("addAccount",wsp)

def on_welcome():
    print('Sesion completada')

# Auth #
socketIO.on('connect', on_connect)
socketIO.on('reconnect', on_reconnect)
socketIO.on('welcome', on_welcome)

socketIO.wait()