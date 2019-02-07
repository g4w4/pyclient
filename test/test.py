from socketIO_client_nexus import SocketIO, LoggingNamespace
from config import infoClient
import os, sys, time, json
from webwhatsapi import WhatsAPIDriver
from webwhatsapi.objects.message import Message, MediaMessage
import shutil


socketIO = SocketIO('127.0.0.1',3000, LoggingNamespace)

def on_connect():
    print('connect')
    socketIO.emit('loginAcount')


# Auth #
socketIO.on('connect', on_connect)

socketIO.wait()