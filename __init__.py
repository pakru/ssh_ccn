import config, time, sys, os, colorama, atexit, threading, logging
#import paramiko
#from colorama import Fore, Back, Style
import modules.cocon_interface as ccn_iface
#import json

def clientClose():
	#global client
	#client.close()
	print('Closing')
	#coconInt.eventForStop.set()

'''
config.login = config.testConfigJson['Cocon'][0]['Login']
config.password = config.testConfigJson['Cocon'][0]['Password']
config.host = config.testConfigJson['Cocon'][0]['Host']
config.port = int(config.testConfigJson['Cocon'][0]['Port'])
'''

#login = str(os.environ.get('COCON_USER'))
#login = 'admin'
#password = str(os.environ.get('COCON_PASS'))
#password = 'password'

#host = str(os.environ.get('SSW_IP'))
#host = '192.168.118.47'
#port = int(os.environ.get('COCON_PORT'))
#port = 8023

coreNode='core1@ecss1'
sipNode='sip1@ecss1'
dsNode='ds1@ecss1'

client = None

print(config.host+':'+format(config.port))

authCoconData = {"%%DEV_USER%%":config.login, "%%DEV_PASS%%":config.password, "%%SERV_IP%%":config.host}
logging.info('Cocon login: ' + config.login +  ' password: ' + config.password + ' host: ' +config.host)
if config.global_ccn_lock:
	coconInt = ccn_iface.coconInterface(authCoconData, show_cocon_output=True,global_ccn_lock=config.global_ccn_lock)
else:
	coconInt = ccn_iface.coconInterface(authCoconData, show_cocon_output=True)
coconInt.eventForStop = threading.Event()
#Поднимаем thread
coconInt.myThread = threading.Thread(target=ccn_iface.ccn_command_handler, args=(coconInt,),daemon=True)
logging.info('Starting cocon interface thread')
coconInt.myThread.start()
#Проверяем, что он жив.
time.sleep(0.2)
if not coconInt.myThread.is_alive():
	print('Can\'t start CCN configure thread')
	logging.error('Can\'t start CCN configure thread')
	sys.exit(1)


'''
client = paramiko.SSHClient()

client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print('Connecting to host: '+ host +' ...') 
#client.connect(hostname=host, username=login, password=password, port=port)
'''
colorama.init(autoreset=True)

atexit.register(clientClose)
