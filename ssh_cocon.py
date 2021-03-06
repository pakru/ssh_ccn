
import paramiko
import time
import sys
import colorama
from colorama import Fore, Back, Style
from ssh_cocon import login, password, host, port, client, sipNode

global login
global password
global host
global port
global client
global sipNode



def executeOnSSH(commandStr):
	paramiko.util.log_to_file('/tmp/ssh_paramiko.ssh')
	client.connect(hostname=host, username=login, password=password, port=port, look_for_keys=False, allow_agent=False)	
	stdin, stdout, stderr = client.exec_command(commandStr)
	data = stdout.read() + stderr.read()
	client.close()
	time.sleep(0.5)
	return data.decode("utf-8")

def domainRemove(dom):
	client.connect(hostname=host, username=login, password=password, port=port, look_for_keys=False, allow_agent=False)
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

def sipTransportSetup(dom,sipIP,sipPort,sipNode=sipNode):
	print('Setting up SIP`s transport')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/set listen_ports list ['+ sipPort +']')
	print(returnedFromSSH)
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/set node_ip ip-set = ipset node = '+ sipNode +' ip = ' + sipIP)
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






