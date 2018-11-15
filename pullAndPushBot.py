import pywikibot
import pprint
import sys
import os.path
import time
from pywikibot import pagegenerators
import operator

class pullAndPushRevisions:
	def __init__(self, test, wikipedia):
			self.siteTest = test
			self.siteWikipedia = wikipedia
			
	def pullAndPush( self, cursor, currentRevision, increment, threshold, useCursorFile,
		sleepInterval, oneRevision ):
		#count = currentRevision
		while 1:
			count = currentRevision
			endCount = currentRevision + increment * 50 # Get 50 revisions
			if oneRevision == True:
				endCount = currentRevision + increment
			revids = ""
			firstOne = True
			while count < endCount:
				if firstOne == True:
					firstOne = False
				else:
					revids = revids + "|"
				revids = revids + str(count)
				count = count + increment
			#pprint.pprint(revids)
			#print(endCount)
			#continue
			#sys.exit()
			pullParameters = {
				'action': 'query',
				'prop': 'revisions',
				'rvslots': 'main',
				'rvprop': 'ids|flags|timestamp|user|userid|comment|content|size|tags',
				#'revids': '123456|123457'
				'revids': revids
			}
			#pprint.pprint(pullParameters)
			pullGen = pywikibot.data.api.Request(
				self.siteWikipedia, parameters=pullParameters )
			pullData = pullGen.submit()
			unsortedRevisions=[]
			revisions = []
			#pprint.pprint ( pullData )
			try:
				pullData['query']['pages']
			except KeyError:
			#if len ( pullData['query']['pages'] ) ==0:
				if currentRevision < threshold:
					currentRevision = endCount
				print ( "Empty; continuing with " + str(currentRevision)
					+ " after sleeping " + str(sleepInterval) + " seconds" )
				time.sleep( sleepInterval )
				continue
			for pageId,page in pullData['query']['pages'].items():
				title = page['title']
				ns = page['ns']
				pageid = page['pageid']
				for thisRevision in page['revisions']:
					thisRevision['title'] = title
					thisRevision['ns'] = ns
					thisRevision['pageid'] = pageid
					unsortedRevisions.append( thisRevision )
			revisions = sorted(unsortedRevisions, key=lambda revision: revision['revid'] )
			#for revision in revisions:
			#	print( revision['revid'] )
			#sys.exit()
			for revision in revisions:
				pushParameters = {
					'action': 'edit',
					'title': 'Revision:' + str(revision['revid']),
					'namespace': revision['ns'],
					'remotetitle': revision['title'],
					'page': revision['pageid'],
					'token': self.siteTest.tokens['edit'],
					'sdtags': '|'.join(revision['tags']),
					'timestamp': revision['timestamp'],
					'remoterev': revision['revid']					
				}
				if 'minor' in revision:
					pushParameters['minor'] = 'true'
				if 'bot' in revision:
					pushParameters['bot'] = 'true'
				# Potentially hidden fields
				pushParameters['deleted'] = 0
				if 'userhidden' in revision:
					pushParameters['deleted'] = pushParameters['deleted'] + 4
					pushParameters['user'] = ''
					pushParameters['userid'] = 0
				else:
					pushParameters['user'] = revision['user']
					pushParameters['userid'] = revision['userid']
				if 'commenthidden' in revision:
					pushParameters['deleted'] = pushParameters['deleted'] + 2
					pushParameters['summary'] = ''
				else:
					pushParameters['summary'] = revision['comment']
				if 'texthidden' in revision['slots']['main']:
					pushParameters['deleted'] = pushParameters['deleted'] + 1
					pushParameters['text'] = ''
					pushParameters['size'] = revision['size']
				else:
					pushParameters['text'] = revision['slots']['main']['*']
				#pprint.pprint(pushParameters)
				pushGen = pywikibot.data.api.Request(
					self.siteTest, parameters=pushParameters )
				pushData = pushGen.submit()
				pprint.pprint(pushData)
				if pushData['edit']['result'] == 'Success':
					#if currentRevision > threshold:
					currentRevision = revision['revid'] + increment
					cursorFilename = 'cursor' + str(cursor) + '.txt'
					if useCursorFile == True:
						f = open( cursorFilename, 'w')
						f.write( str( currentRevision ) + "\n" )
						f.close()
				else:
					print ( 'Edit failure' )
					pprint.pprint(pushData['edit']['result'])
					sys.exit()
				if oneRevision == True:
					sys.exit()
		
siteTest = pywikibot.Site(code='en', fam='test2')
if not siteTest.logged_in():
    siteTest.login()
siteWikipedia = pywikibot.Site(code='en', fam='wikipedia')
# Defaults
cursor = 0
currentRevision = 0
increment = 10
threshold = 800000000 # 900 million
sleepInterval = 3
useCursorFile = True
oneRevision = False
if len(sys.argv) < 2:
	print ( 'Usage: python pullAndPushBot.py [--cursor] [--increment] [--currentrevision] [--threshold] [--onerevision]' )
	print ( '--cursor is the offset' )
	print ( '--currentrevision is the starting revision' )
	print ( '--threshold sets a revid after which bad revisions are not skipped' )
	print ( '--onerevision stops after one revision' )
	print ( 'Example: python pullAndPushBot.py --cursor=1' )
	print ( 'Example: python pullAndPushBot.py --currentrevision=8000001' )
	print ( 'Example: python pullAndPushBot.py --currentrevision=8000001 --onerevision' )
	sys.exit()
# Command line arguments
for arg in sys.argv:
	if arg[0:9] == '--cursor=':
		cursor = int( arg[9:] )
	if arg[0:12] == '--increment=':
		cursor = int( arg[12:] )
	if arg[0:18] == '--currentrevision=':
		currentRevision = int( arg[18:] )
	if arg[0:12] == '--threshold=':
		threshold = int( arg[12:] )
	if arg[0:12] == '--sleepinterval=':
		threshold = int( arg[12:] )
	if arg[0:13] == '--onerevision':
		oneRevision = True
		useCursorFile = False
	#print ( arg )
	#print ( arg[0:18] )
	#print ( arg[18:] )
if cursor == 0:
	if currentRevision == 0:
		print ( 'You must use either the --cursor or --currentrevision argument' )
		sys.exit()
	else:
		cursor = currentRevision % increment
cursorFilename = 'cursor' + str(cursor) + '.txt'
# Command line current revision overrides cursor file
if currentRevision == 0 and os.path.isfile( cursorFilename ):
	f = open( cursorFilename, 'r')
	currentRevision = int( f.readline() )
myTestScript = pullAndPushRevisions( siteTest, siteWikipedia )
if ( currentRevision % increment != cursor ):
	print ( 'Error: Modulus is ' + str( currentRevision % increment ) )
	sys.exit()
print ( 'Resuming with ' + str( currentRevision ) )
myTestScript.pullAndPush( cursor, currentRevision, increment, threshold, useCursorFile,
	sleepInterval, oneRevision )