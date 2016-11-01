
import paramiko
import time
import sys
import colorama
from colorama import Fore, Back, Style
from ssh_cocon import login, password, host, port, client

global login
global password
global host
global port
global client


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
		print('Domain exists... needs to remove')
		return True
	else:
		print('Domain "'+ dom +'" is not exists...')
		return False
	return False


def domainDeclare(dom):
	if checkDomainExist(dom):
		print('Domain exists... needs to remove')
		domainRemove(dom)
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

