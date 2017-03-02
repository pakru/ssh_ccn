
import paramiko
import time
import sys
import colorama
from colorama import Fore, Back, Style
from ssh_cocon import coconInt
import config
import modules.cocon_interface as ccn_iface
import threading

'''
global login
global password
global host
global port
global client
global sipNode
global coconInt
'''



def executeOnSSH(commandStr, cutHead = True):
	'''
	paramiko.util.log_to_file('/tmp/ssh_paramiko.ssh')
	client.connect(hostname=host, username=login, password=password, port=port, look_for_keys=False, allow_agent=False)	
	stdin, stdout, stderr = client.exec_command(commandStr)
	data = stdout.read() + stderr.read()
	client.close()
	time.sleep(0.5)
		'''
	#test = '/node/uptime\nsystem-status\n'

	# ccn_iface.cocon_push_string_command(coconCommands,coconInt)

	#print('sending string')
	ccn_iface.cocon_push_string_command(coconCommands=commandStr+'\n', coconInt = coconInt)

	#payloadFromCocon = coconInt.data.splitlines(True)[2:]
	endCutPosition = coconInt.data.decode('utf-8').find(':/$ exit')
	if cutHead:
		startCutPosition = coconInt.data.decode('utf-8').find('\n')
		return coconInt.data.decode('utf-8')[startCutPosition:endCutPosition]
	else:
		return coconInt.data.decode('utf-8')[:endCutPosition]

	#print('endCut pos: ' + str(endCutPosition))
	#print('recieved: ')
	#print(coconInt.data.decode('utf-8'))
	#print('--------------Enter found at: ' + str(coconInt.last_data.decode('utf-8').find('\n')))


	#return payloadFromCocon

def domainRemove(dom):
	client = paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	client.connect(hostname=config.host, username=config.login, password=config.password, port=config.port, look_for_keys=False, allow_agent=False)
	chan = client.invoke_shell()
	chan.send('domain/remove ' +dom+ '\n')
	buff = ''
	while not buff.endswith('Are you sure?: yes/no ?> '):
		resp = chan.recv(9999)
		buff += resp.decode("utf-8")
	#print(buff)
	chan.send('yes\n')
	buff = ''
	while not buff.endswith(']:/$ '):
		resp = chan.recv(9999)
		buff += resp.decode("utf-8")
	print('Removing domain...')
	print(buff)
	client.close()
	return True

def checkDomainExist(dom):
	print('Checking if test domain exist...')
	returnedFromSSH = executeOnSSH('domain/list')
	print(returnedFromSSH)
	if dom in returnedFromSSH: # проверка наличия текста в выводе
		print('Domain exists!')
		return True
	else:
		print('Domain "'+ dom +'" is not exists!')
		return False
	return False


def domainDeclare(dom, removeIfExists = False):
	if checkDomainExist(dom):
		if removeIfExists:
			print('Removing domain due to its existance!')
			domainRemove(dom)
		else:
			print('Domain already exists')
			return True
	else:
		print('Creating domain "'+ dom +'"')

	print('Declaring domain...')
	returnedFromSSH = executeOnSSH('domain/declare ' + dom + ' --add-domain-admin-privileges --add-domain-user-privileges')
	print(returnedFromSSH)
	if 'declared' in returnedFromSSH: # проверка наличия текста в выводе
		return True
	else:
		return False

def checkDomainInit(dom):
	print('Checking domain creation...')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/info share_set ')
	print(returnedFromSSH)
	if 'share_set' in returnedFromSSH:
		return True
	else:
		return False	

def sipTransportSetup(dom,sipIP,sipPort,sipNode=config.sipNode):
	print('Setting up SIP`s transport')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/set listen_ports list ['+ sipPort +']')
	print(returnedFromSSH)
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/set node_ip ip-set = ipset node = '+ sipNode +' ip = ' + sipIP)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		return True
	else: 
		return False

def sipTransportShareSetup(dom,sharesetName):
	print('Set on domain SIP share set')
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/sip/network/set share_set '+sharesetName)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		return True
	else:
		return False


def sipShareSetDeclare(sipIP,sipPort,sharesetName,sipNode=config.sipNode):
	print('Declaring SIP share set')
	returnedFromSSH = executeOnSSH('cluster/adapter/sip1/sip/network/set share_set '+ sharesetName +
								   ' node-ip node = '+ sipNode +' = '+ sipIP)
	print(returnedFromSSH)
	returnedFromSSH = executeOnSSH('cluster/adapter/sip1/sip/network/set share_set '+ sharesetName +
								   ' listen-ports list = ['+ sipPort +']')
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		return True
	else:
		return False


def trunkDeclare(dom,trunkName,trunkGroup,routingCTX,sipIPset,sipPort,destSipIP,destSipPort):
	print('Declaring SIP trunk...')
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/trunk/sip/declare '+ routingCTX +' '+ trunkGroup +' '+ trunkName +' '+ sipIPset +' '+ destSipIP +' '+ destSipPort +' sip-proxy '+ sipPort)
	print(returnedFromSSH)
	if 'declared' in returnedFromSSH:
		return True
	else:
		return False

def setTraceMode(dom,traceMode):
	print('Setting trace mode to ' + traceMode  + ' for domain '+ dom)
	returnedFromSSH = executeOnSSH('domain/' + dom + '/trace/properties/set mode ' + traceMode)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		return True
	else: 
		return False

def setLogging(node,logRule,action):
	print('Set logging of '+ node +' ' + logRule + ' to ' + action )
	print('This action can take a few minutes. Be patient!')
	returnedFromSSH = executeOnSSH('node/'+ node +'/log/config rule '+logRule+' '+action)
	print(returnedFromSSH)
	if 'Successful' in returnedFromSSH:
		return True
	else:
		return False

def setSysIfaceRoutung(dom,sysIface,routingCTX):
	print('Setting routing ctx to iface system:teleconference...')
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/system-iface/set '+ sysIface +' routing.context '+ routingCTX)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		return True
	else:
		return False

def subscribersCreate(dom,sipNumber,sipPass,sipGroup,routingCTX):
	print('Declaring Subscriber(s):... '+ sipNumber + ' ...')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/user/declare '+ routingCTX +' '+ sipGroup +' '+ sipNumber+'@'+ dom +' none no_qop_authentication login-as-number '+ sipPass)
	print(returnedFromSSH)
	if subscriberSipInfo(dom,sipNumber,sipGroup,complete=False):
		return True
	else:
		return False

def subscriberSipInfo(dom,sipNumber,sipGroup,complete=False):
	if complete:
		returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/user/info '+ sipGroup +' '+ sipNumber + '@'+ dom + ' --complete')
	else:
		returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/user/info '+ sipGroup +' '+ sipNumber + '@'+ dom)
	print(returnedFromSSH)
	if 'internal iface name' in returnedFromSSH:
		return True
	else:
		return False


def ssEnable(dom,subscrNum,ssNames):
	print('Enabling services: '+ ssNames + ' for ' + subscrNum)
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/ss/enable '+ subscrNum +' ' + ssNames)
	print(returnedFromSSH)
	if 'Success:' in returnedFromSSH:
		return True
	else:
		return False

def ssActivation(dom,subscrNum,ssName,ssOptions=''):
	if ssOptions is '':
		print('Activating service: '+ ssName + ' for ' + subscrNum)
	else:
		print('Activating service: '+ ssName + ' for ' + subscrNum + ' with options: '+ ssOptions)

	returnedFromSSH = executeOnSSH('domain/'+ dom +'/ss/activate '+ subscrNum +' '+ ssName +' '+ ssOptions)
	print(returnedFromSSH)
	if 'Success:' in returnedFromSSH:
		return True
	else:
		return False

def ssAddAccess(dom,ssName,dsNode='ds1'):
	print('Adding access to supplementary services for domain :'+ dom)
	returnedFromSSH = executeOnSSH('cluster/storage/'+dsNode+'/ss/access-list add ' + dom + ' ' + ssName)
	print(returnedFromSSH)
	if 'successfully' in returnedFromSSH:
		return True
	else:
		return False

def ssAddAccessAll(dom,dsNode='ds1'):
	return ssAddAccess(dom=dom,ssName='*',dsNode=dsNode)

def tcRestHostSet(restHost,restPort):
	print('Setting restHost and restPort...')
	returnedFromSSH = executeOnSSH('system/tc/properties/set * rest_host ' + restHost)
	#print(returnedFromSSH)
	if not 'successfully changed' in returnedFromSSH:
		print(returnedFromSSH)
		return False
	returnedFromSSH = executeOnSSH('system/tc/properties/set * rest_port ' + restPort)
	if not 'successfully changed' in returnedFromSSH:
		print(returnedFromSSH)
		return False
	return True

def subscriberPortalSetConnection(dom, host='localhost', login='subscribers', passwd='subscribers', dbName='ecss_subscribers'):
	print('Set SubscriberPortal connection properties')
	returnedFromSSH = executeOnSSH('domain/' + dom +'/subscriber-portal/properties/set connection ' + host + ' ' + login
								   + ' ' + passwd + ' ' + dbName)
	print(returnedFromSSH)
	if not 'successfully changed' in returnedFromSSH:
		#print(returnedFromSSH)
		return False
	return True

def subscriberPortalCheckConnection(dom):
	print('Check subscriber portal MySQL connection...')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/subscriber-portal/check-connection')
	print(returnedFromSSH)
	if 'Connection successful' in returnedFromSSH:
		print(returnedFromSSH)
		return True
	else:
		return False

def setAliasSubscriberPortalLoginPass(dom, subscrNum, sipGroup, login, passwd):
	print('Set subscriber portal login/pass...')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/alias/set ' + subscrNum + ' ' + sipGroup + ' ' + subscrNum + '@' + dom +
								   ' subscriber_portal\login ' + '"' + login + '"')
	print(returnedFromSSH)
	#if not 'affected by settings property' in returnedFromSSH:
		#print(returnedFromSSH)
		#return False
	#time.sleep(0.5)
	returnedFromSSH = executeOnSSH('domain/' + dom + '/alias/set ' + subscrNum + ' ' + sipGroup + ' ' + subscrNum + '@' + dom +
								   ' subscriber_portal\password ' + '"' + passwd + '"')
	print(returnedFromSSH)
	if not 'affected by settings property' in returnedFromSSH:
		#print(returnedFromSSH)
		return False
	return True

