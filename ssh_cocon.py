import logging
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
	logging.debug('Send via SSH: ' + commandStr)
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
	time.sleep(2)
	logging.info('Removing domain: ' + dom)

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
	logging.info('Domain removed')
	print('Removing domain...')
	print(buff)
	client.close()
	return True

def checkDomainExist(dom):
	print('Checking if test domain exist...')
	logging.info('Checking if '+dom+' domain exist')
	returnedFromSSH = executeOnSSH('domain/list')
	print(returnedFromSSH)
	if dom in returnedFromSSH: # проверка наличия текста в выводе
		print('Domain exists!')
		logging.info('Domain "'+ dom +'" exists!')
		return True
	else:
		print('Domain "'+ dom +'" is not exists!')
		logging.info('Domain "' + dom + '" is not exists!')
		return False

def domainDeclare(dom, removeIfExists = False):
	logging.info('Declaring ' + dom + ' domain')
	if checkDomainExist(dom):
		if removeIfExists:
			print('Removing domain due to its existance!')
			logging.info('Removing domain due to its existance!')
			domainRemove(dom)
		else:
			print('Domain already exists')
			logging.info('Domain already exists')
			return True
	else:
		print('Creating domain "'+ dom +'"')
		logging.info('Creating domain "'+ dom +'"')

	print('Declaring domain...')
	returnedFromSSH = executeOnSSH('domain/declare ' + dom + ' --add-domain-admin-privileges --add-domain-user-privileges')
	print(returnedFromSSH)
	if 'declared' in returnedFromSSH: # проверка наличия текста в выводе
		logging.info('Domain "' + dom + '" created')
		return True
	else:
		logging.error('Domain "' + dom + '" failed created')
		return False

def checkDomainInit(dom):
	print('Checking domain creation...')
	logging.info('Checking domain"' + dom + '" initialisation')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/info share_set ')
	print(returnedFromSSH)
	if 'share_set' in returnedFromSSH:
		logging.info('Domain "' + dom + '" initialised')
		return True
	else:
		logging.info('Domain "' + dom + '" is not initialised')
		return False	

def sipTransportSetup(dom,sipIP,sipPort,sipNode=config.sipNode):
	print('Setting up SIP`s transport')
	logging.info('Setting up SIP ipset of "' + dom + '" domain')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/set listen_ports list ['+ sipPort +']')
	print(returnedFromSSH)
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/network/set node_ip ip-set = ipset node = '+ sipNode +' ip = ' + sipIP)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		logging.info('SIP ipset of "' + dom + '" domain is successfully set')
		return True
	else:
		logging.error('Failed to set SIP ipset of "' + dom + '" domain')
		return False

def sipTransportShareSetup(dom,sharesetName):
	print('Set on domain SIP share set')
	logging.info('Setting up SIP shareset of "' + dom + '" domain')
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/sip/network/set share_set '+sharesetName)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		logging.info('SIP shareset of "' + dom + '" domain is successfully set')
		return True
	else:
		logging.error('Failed to set SIP shareset of "' + dom + '" domain')
		return False

def sipShareSetDeclare(sipIP,sipPort,sharesetName,sipNode=config.sipNode):
	print('Declaring SIP share set')
	logging.info('Declaring SIP share set')
	returnedFromSSH = executeOnSSH('cluster/adapter/sip1/sip/network/set share_set '+ sharesetName +
								   ' node-ip node = '+ sipNode +' = '+ sipIP)
	print(returnedFromSSH)
	returnedFromSSH = executeOnSSH('cluster/adapter/sip1/sip/network/set share_set '+ sharesetName +
								   ' listen-ports list = ['+ sipPort +']')
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		logging.info('SIP shareset successfully declared')
		return True
	else:
		logging.info('Failed to declare shareset')
		return False


def trunkDeclare(dom,trunkName,trunkGroup,routingCTX,sipIPset,sipPort,destSipIP,destSipPort):
	print('Declaring SIP trunk...')
	logging.info('Declaring SIP trunk "' + trunkName + '" in "' + dom + '" domain')
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/trunk/sip/declare '+ routingCTX +' '+ trunkGroup +' '+ trunkName +' '+ sipIPset +' '+ destSipIP +' '+ destSipPort +' sip-proxy '+ sipPort)
	print(returnedFromSSH)
	if 'declared' in returnedFromSSH:
		logging.info('SIP trunk "'+ trunkName +'" successfully declared')
		return True
	else:
		logging.error('Failed to declare SIP trunk "' + trunkName + '"')
		return False

def setTraceMode(dom,traceMode):
	print('Setting trace mode to ' + traceMode  + ' for domain '+ dom)
	logging.info('Setting trace mode to ' + traceMode  + ' for domain "'+ dom + '"')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/trace/properties/set mode ' + traceMode)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		logging.info('Trace mode for domain "'+ dom + '" is set')
		return True
	else:
		logging.error('Failed to set tracemode for "' + dom + '" is set')
		return False

def setLogging(node,logRule,action):
	print('Set logging of '+ node +' ' + logRule + ' to ' + action )
	logging.info('Set logging of '+ node +' ' + logRule + ' to ' + action )
	print('This action can take a few minutes. Be patient!')
	returnedFromSSH = executeOnSSH('node/'+ node +'/log/config rule '+logRule+' '+action)
	print(returnedFromSSH)
	if 'Successful' in returnedFromSSH:
		logging.info('Logging of ' + node + ' ' + logRule + ' is successfully set to ' + action)
		return True
	else:
		logging.error('Failed to set Logging of ' + node )
		return False

def setSysIfaceRoutung(dom,sysIface,routingCTX):
	print('Setting routing ctx of ' + sysIface + ' in "'+ dom +'"')
	logging.info('Setting routing ctx of ' + sysIface + ' in "'+ dom +'"')
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/system-iface/set '+ sysIface +' routing.context '+ routingCTX)
	print(returnedFromSSH)
	if 'successfully changed' in returnedFromSSH:
		logging.info('Sys interface ' + sysIface + ' routing ctx changed for domain "' + dom + '"')
		return True
	else:
		logging.error('Failed to set routing ctx of sys interface ' + sysIface + ' in domain "' + dom + '"')
		return False

def subscribersCreate(dom,sipNumber,sipPass,sipGroup,routingCTX):
	print('Declaring Subscriber(s):... '+ sipNumber + ' ...')
	logging.info('Declaring Subscriber(s): ' + sipNumber + ' for domain "' + dom + '"')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/user/declare '+ routingCTX +' '+ sipGroup +' '+ sipNumber+'@'+ dom +' none no_qop_authentication login-as-number '+ sipPass)
	print(returnedFromSSH)
	if subscriberSipInfo(dom,sipNumber,sipGroup,complete=False):
		logging.info('Subscriber(s): ' + sipNumber + ' successdully created for domain "' + dom + '"')
		return True
	else:
		logging.info('Failed to create subscriber(s): ' + sipNumber + ' for domain "' + dom + '"')
		return False

def subscriberSipInfo(dom,sipNumber,sipGroup,complete=False):
	logging.debug('Get SIP info for: ' + sipNumber + ' domain "' + dom + '"')
	if complete:
		returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/user/info '+ sipGroup +' '+ sipNumber + '@'+ dom + ' --complete')
	else:
		returnedFromSSH = executeOnSSH('domain/' + dom + '/sip/user/info '+ sipGroup +' '+ sipNumber + '@'+ dom)
	print(returnedFromSSH)
	if 'internal iface name' in returnedFromSSH:
		logging.debug('Success SIP info get for: ' + sipNumber + ' domain "' + dom + '"')
		return True
	else:
		logging.warning('Failed to get SIP info for: ' + sipNumber + ' domain "' + dom + '"')
		return False


def ssEnable(dom,subscrNum,ssNames):
	print('Enabling services: '+ ssNames + ' for ' + subscrNum)
	logging.info('Enabling services: '+ ssNames + ' for ' + subscrNum + ' in domain "' + dom + '"')
	returnedFromSSH = executeOnSSH('domain/'+ dom +'/ss/enable '+ subscrNum +' ' + ssNames)
	print(returnedFromSSH)
	if 'Success:' in returnedFromSSH:
		logging.info('Successful enabled services: ' + ssNames + ' for ' + subscrNum + ' in domain "' + dom + '"')
		return True
	else:
		logging.error('Failed to enable services: ' + ssNames + ' for ' + subscrNum + ' in domain "' + dom + '"')
		return False

def ssActivation(dom,subscrNum,ssName,ssOptions=''):
	if ssOptions is '':
		print('Activating service: '+ ssName + ' for ' + subscrNum)
		logging.info('Activating service: '+ ssName + ' for ' + subscrNum)
	else:
		print('Activating service: '+ ssName + ' for ' + subscrNum + ' with options: '+ ssOptions)
		logging.info('Activating service: '+ ssName + ' for ' + subscrNum + ' with options: '+ ssOptions)

	returnedFromSSH = executeOnSSH('domain/'+ dom +'/ss/activate '+ subscrNum +' '+ ssName +' '+ ssOptions)
	print(returnedFromSSH)
	if 'Success:' in returnedFromSSH:
		logging.info('Successful activated service: ' + ssName + ' for ' + subscrNum + ' in domain "' + dom + '"')
		return True
	else:
		logging.error('Failed to activate service: ' + ssName + ' for ' + subscrNum + ' in domain "' + dom + '"')
		return False

def ssAddAccess(dom,ssName,dsNode='ds1'):
	print('Adding access to supplementary services for domain :'+ dom)
	logging.info('Adding access to supplementary services' + ssName + ' for domain :'+ dom)
	returnedFromSSH = executeOnSSH('cluster/storage/'+dsNode+'/ss/access-list add ' + dom + ' ' + ssName)
	print(returnedFromSSH)
	if 'successfully' in returnedFromSSH:
		logging.info('Supplementary services successfully added to access list for domain :' + dom)
		return True
	else:
		logging.error('Failed to add Supplementary services to access list for domain :' + dom)
		return False

def ssAddAccessAll(dom,dsNode='ds1'):
	return ssAddAccess(dom=dom,ssName='*',dsNode=dsNode)

def tcRestHostSet(restHost,restPort):
	print('Setting restHost and restPort...')
	logging.info('Setting restHost and restPort')
	returnedFromSSH = executeOnSSH('system/tc/properties/set * rest_host ' + restHost)
	#print(returnedFromSSH)
	if not 'successfully changed' in returnedFromSSH:
		logging.error('Failed to set restHost')
		print(returnedFromSSH)
		return False
	returnedFromSSH = executeOnSSH('system/tc/properties/set * rest_port ' + restPort)
	if not 'successfully changed' in returnedFromSSH:
		logging.error('Failed to set restPort')
		print(returnedFromSSH)
		return False
	logging.info('restHost and restPort successfully set')
	return True

def subscriberPortalSetConnection(dom, host='localhost', login='subscribers', passwd='subscribers', dbName='ecss_subscribers'):
	print('Set SubscriberPortal connection properties')
	logging.info('Set SubscriberPortal connection properties for domain "' + dom + '"')
	returnedFromSSH = executeOnSSH('domain/' + dom +'/subscriber-portal/properties/set connection ' + host + ' ' + login
								   + ' ' + passwd + ' ' + dbName)
	print(returnedFromSSH)
	if not 'successfully changed' in returnedFromSSH:
		logging.error('Failed to set SubscriberPortal connection properties for domain "' + dom + '"')
		return False
	logging.info('SubscriberPortal connection properties successfully set for domain "' + dom + '"')
	return True

def subscriberPortalCheckConnection(dom):
	print('Check subscriber portal MySQL connection...')
	returnedFromSSH = executeOnSSH('domain/' + dom + '/subscriber-portal/check-connection')
	print(returnedFromSSH)
	if 'Connection successful' in returnedFromSSH:
		logging.info('SubscriberPortal connection test successful for "' + dom + '"')
		print(returnedFromSSH)
		return True
	else:
		logging.warning('SubscriberPortal connection test failed for "' + dom + '"')
		return False

def setAliasSubscriberPortalLoginPass(dom, subscrNum, sipGroup, login, passwd):
	print('Set subscriber portal login/pass...')
	logging.info('Set subscriberPortal login/password of subscriber ' + subscrNum +' in domain "' + dom + '"')
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
		logging.error('Failed to set subscriberPortal login/password of subscriber ' + subscrNum + ' in domain "' + dom + '"')
		#print(returnedFromSSH)
		return False
	logging.info('SubscriberPortal login/password of subscriber ' + subscrNum + ' successfully set in domain "' + dom + '"')
	return True

