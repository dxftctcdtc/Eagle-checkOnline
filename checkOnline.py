# -*- coding:utf-8 -*-
#author: Song Bo, Eagle, ZJU
#email: sbo@zju.edu.cn

import urllib
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
import cookielib
import sys
import re

version = 'V0.3.1'
date = '2014-7-24'


headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Accept-Encoding':'gzip,deflate,sdch',
		'Accept-Language':'en,zh-CN;q=0.8,zh;q=0.6',
		'Cache-Control':'max-age=0',
		'Connection':'keep-alive',
		'Content-Type':'application/x-www-form-urlencoded',
		'Host':'10.214.52.238:8080',
		'Origin':'http://10.214.52.238:8080',
		'Referer':'http://10.214.52.238:8080/OnlineCheck/login',
		'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
	}
ipAddress = 'http://10.214.52.238:8080'
taskItemURL = ipAddress + '/OnlineCheck/taskitem'
loginURL = ipAddress + '/OnlineCheck/login'
applyTaskURL = ipAddress + '/OnlineCheck/taskitem/applytask'

username = ''
password = ''

def chmod(mes, encoding ='utf-8'):
	if isinstance(mes, unicode):
		return mes.encode(encoding)

	for c in ('utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16'):
		try:
			if encoding == 'unicode':
				return mes.decode(c)
			else:
				return mes.decode(c).encode(encoding)
		except:
			pass
	raise 'Unknown charset'

def myFormat(string, length=0):
	if length == 0:
		return string
	slen = len(string)
	re = string
	if isinstance(string, str):
		placeholder = ' '
	else:#if chinese string, we use quanjiao space
		placeholder = u'　'
	while slen < length:
		re += placeholder
		slen += 1
	return re
def login(username, password):

	#构造登陆post表单
	postData = 'username=%s&password=%s' %(username, password)
	#记录cookies并下载到本地
	cj = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)
	
	#下载登陆界面cookies
	testReq = Request(loginURL, headers = headers)
	urlopen(testReq)

	#提交表单，登陆
	#模拟浏览器的Headers
	req = Request(loginURL, postData, headers)
	res = urlopen(req)
	if res.getcode() != 200:
		print 'Can not connect to the server. Please check your network connection.'
		sys.exit()
		return False
	if res.geturl() == taskItemURL:
		return True
	else:
		return False
def applyTask(minWebID, maxWebID, taskID = None):
	if not isLogin():
		print 'Session expired. Login again...'
		login(username, password)
	nTask = 0
	req = Request(applyTaskURL, headers = headers)
	html = urlopen(req).read()
	options = re.findall('''<option value="(.*)" ''', html, re.I)
	nOptions = []
	hostIDs = []
	for option in options:
		if option == None or len(option) <= 3:
			continue
		value = option.split(",")[0]
		if int(value) <= maxWebID and int(value) >= minWebID:
			hostIDs.append(value)
			nOptions.append(option)
		else:
			continue

	#get available task types
	for idx in range(len(hostIDs)):
		taskTypeURL = 'http://10.214.52.238:8080/OnlineCheck/ajax/tasktype/%s' % hostIDs[idx]
		req = Request(taskTypeURL, headers = headers)
		html = urlopen(req).read()
		taskTypeValues = re.findall(''',(\d+)"''',html,re.I)
		for taskTypeValue in taskTypeValues:
			if int(taskTypeValue) ==  taskID or taskID == None:
				#get task title
				taskTitleURL = 'http://10.214.52.238:8080/OnlineCheck/ajax/tasktitle'
				taskTitlePostData = {"hostid":"%s" % hostIDs[idx],
						"hostname":"%s" % nOptions[idx].split(',')[1]
						}
				taskTitlePostData = urllib.urlencode(taskTitlePostData)
				req = Request(taskTitleURL,taskTitlePostData, headers)
				res = urlopen(req)
				taskTitle = re.search(''':"(.*)"''',res.read())
				taskTitle = taskTitle.group(1)

				bigtasktype = ''
				taskrule = int(taskTypeValue)
				task_length_small = 1
				task_length_big = 100

				postData = {'hostidname':'%s' % nOptions[idx],
						'bigtasktype':'%s' % bigtasktype,
						'taskrule':'%s' % taskrule,
						'task_length_small':'%s' % task_length_small,
						'task_length_big':'%s' % task_length_big,
						'tasktitle':'%s' % taskTitle
				}
				print "%s" %taskTitle.decode("utf-8"), taskTypeValue
				nTask += 1
				postData = urllib.urlencode(postData)
				req = Request(applyTaskURL, postData, headers)
				res = urlopen(req)
	print "Apply %s tasks successfully." % nTask
def fetchAvaliabletasks():

	req = Request(applyTaskURL, headers = headers)
	html = urlopen(req).read()
	options = re.findall('''<option value="(.*)" ''', html, re.I)
	nOptions = []
	print "ID\t\tName\t\tPriority"
	for option in options:
		if len(option) <= 4:
			continue
		nOptions.append(option)
		idx,name,priority = option.decode("utf-8").split(",")
		print idx,'\t',name,'\t',priority
	return options

def applyTasks():
	print 'Fetching avaliable tasks...'
	websites = fetchAvaliabletasks()
	try:
		websiteID = int(raw_input('Please enter the website id you want to apply tasks from(enter 0 to return): '))
	except ValueError,e:
		print 'websiteID is unavailable.'
		return False
	except KeyboardInterrupt,e:
		return True
	if websiteID == 0:
		return True
	applyTask(websiteID,websiteID)
def fetchPendingTasks():
	if not isLogin():
		print 'Session expired. Login again...'
		login(username, password)
	req = Request(taskItemURL+'''?pageSize=50''',headers=headers)
	res = urlopen(req)
	html = res.read()
	content = re.search('''<table \s* id="todoTable" .*? </table>''',html,re.X|re.DOTALL).group(0) #find content table
	items = re.findall('''<tr>\s* 					# start of the content table
			<td \s* align="center">(.*?)</td>\s*      #name of the website
			<td \s* align="center"><a \s href="/OnlineCheck/taskitem/taskdetail/(\d+)">(\d+)</a></td>\s*  #task id and task size
			<td \s* align="center">([\d.\s]+)</td>\s* 	#rule id
			<td \s* align="center">(.*?)</td>\s*	#rule name
			<td \s* align="center">\s*<a \s* href="/OnlineCheck/taskitem/check/   #task is ready to check
			.*?</tr>''',content,re.DOTALL|re.X)
	#print pending tasks
	if items == []:
		print 'No pending tasks in your account so far. Please apply at least one at first.'
		return False
	print 'taskID  rule name                        ruleID size website name'
	taskIDs=[]
	for item in items:
		print ' ' + myFormat(item[1],5) + myFormat(item[4].decode('utf-8'),18) + myFormat(item[3], 7) + myFormat(item[2], 3) + myFormat(item[0].decode('utf-8'))
		taskIDs.append(int(item[1]))
	#item[0] = website name
	#item[1] = task id
	#item[2] = task size
	#item[3] = rule id
	#item[4] = rule name
	return taskIDs
def passTestPages():
	taskIDs = fetchPendingTasks()
	if taskIDs == False:
		return False
	try:
		isBreak = False
		while True:
			if isBreak == True:
				break 
			isBreak = True
			taskIDs = raw_input('Please enter the task id you want to pass(enter 0 to return): ').split(' ')
			#taskID = int(raw_input('Please enter the task id you want to pass(enter 0 to return): '))
			for taskID in taskIDs:
				taskID = int(taskID)
				if taskID == 0:
					return True
				if str(taskID) not in taskIDs:
					print 'Illegal taskID. taskID is not in the list. Please enter it again'
					isBreak = False
	except:
		print 'Illegal taskID'
		return False
	if not isLogin():
		print 'Session expired. Login again...'
		login(username, password)
	#enter check page
	nPage = 0
	for taskID in taskIDs:
		checkPageURL = taskItemURL+ '/check/' + taskID
		req = Request(checkPageURL,headers = headers)
		while True:
			res = urlopen(req)
			if res.geturl() == taskItemURL: #finished
				break
			html = res.read()

			#get test page url
			testPageURL = re.search('''<td><a href="([^"]+)" target="blank">''',html).group(1)

			#get rule id
			ruleID = re.search('''input name="ruleid" type="hidden" value="(\d+)"''',html).group(1)
			ruleID = int(ruleID)

			#get submit url
			submitURL = re.search('''<form\saction="([\w/]+)"\smethod="post"''',html).group(1)
			submitURL = ipAddress + submitURL
			postData = {"ruleid":"%s" % ruleID,"checkresult":"1","optionsRadios":"1","frequentmessage":"","message":""}
			postData = urllib.urlencode(postData)
			req = Request(submitURL,postData, headers = headers)
			nPage+=1
			print testPageURL + '---Pass'
		
	print 'Pass %s pages successfully.' %nPage

def rejectTestPages():
	taskIDs = fetchPendingTasks()
	if taskIDs == False:
		return False
	try:
		while True:
			taskID = int(raw_input('Please enter the task id you want to reject(enter 0 to return): '))
			if taskID == 0:
				return True
			if taskID not in taskIDs:
				raise ValueError, 'Illegal taskID. taskID is not in the list. Please enter it again'
			mes = raw_input('Please enter reject reason: ')
			break
	except ValueError,e:
		print e
		return False
	except KeyboardInterrupt, e:
		print 'Exit the program.'
		sys.exit()
	if not isLogin():
		print 'Session expired. Login again...'
		login(username, password)
	#enter check page
	checkPageURL = taskItemURL+ '/check/' + str(taskID)
	req = Request(checkPageURL,headers = headers)
	nPage = 0
	while True:
		res = urlopen(req)
		if res.geturl() == taskItemURL: #finished
			break
		html = res.read()
		#get test page url
		testPageURL = re.search('''<td><a href="([^"]+)" target="blank">''',html).group(1)

		#get rule id
		ruleID = re.search('''input name="ruleid" type="hidden" value="(\d+)"''',html).group(1)
		ruleID = int(ruleID)

		#get submit url
		submitURL = re.search('''<form\saction="([\w/]+)"\smethod="post"''',html).group(1)
		submitURL = ipAddress + submitURL
		postData = {"ruleid":"%s" % ruleID,"checkresult":"0","optionsRadios":"0","frequentmessage":"","message":"%s" %chmod(mes, "utf-8")}
		postData = urllib.urlencode(postData)
		print postData
		return
		req = Request(submitURL,postData, headers = headers)
		nPage+=1
		print testPageURL + '---Reject: ' + mes
		
	print 'Reject %s pages successfully.' %nPage

def isLogin():
	req = Request(taskItemURL,headers=headers)
	res = urlopen(req)
	if res.geturl() == taskItemURL:
		return True
	else:
		return False

def main():
	global username, password
	print 'Welcome to Web Accessibility Initiative Script. %s ' % version
	print 'Eagle, ZJU. %s' % date
	username = raw_input('Please enter your username: ')
	#username = 'songbo'
	import getpass
	password = getpass.getpass('Please enter your password(not be shown): ')
	#password = '123456'
	print 'Login...'
	if login(username,password) == False:
		print "Login failed. Please check your username or password. "
		return
	print 'Login success.'
	while True:
		try:
			print '''\nAvailable tasks:				
		1. Apply tasks.
		2. Pass test pages.
		3. Reject test pages.
		0. Exit.
			'''
			taskID = int(raw_input('Please enter task id(0-3): '))
			if taskID < 0 or taskID > 3:
				raise ValueError, 'Invalid task id'
		except ValueError, e:
			print e
		except KeyboardInterrupt, e:
			return

		else:
			if isLogin() == False:
				print 'Session expired. Login again...'
				login(username, password)
			if taskID == 1:
				applyTasks()
			elif taskID == 2:
				passTestPages()
			elif taskID == 3:
				rejectTestPages()
			elif taskID == 0:
				break

if __name__ == '__main__':
	main()
	
