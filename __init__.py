import paramiko
import time
import sys
import os
import colorama
from colorama import Fore, Back, Style
import atexit

def clientClose():
	global client
	client.close()


login = str(os.environ.get('COCON_USER'))
password = str(os.environ.get('COCON_PASS'))

host = str(os.environ.get('SSW_IP'))
port = int(os.environ.get('COCON_PORT'))

print(host+':'+format(port))

client = paramiko.SSHClient()

client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print('Connecting to host: '+ host +' ...') 
#client.connect(hostname=host, username=login, password=password, port=port)
colorama.init(autoreset=True)

atexit.register(clientClose)
