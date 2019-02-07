import pywikibot
import pprint
import sys
import os.path
import time
import MySQLdb
from pywikibot import pagegenerators
import operator
#import HTMLParser
from xml.sax.saxutils import unescape

class pullAndPushRevisions:
	def __init__(self, test, wikipedia):
			self.siteTest = test
			self.siteWikipedia = wikipedia
			
	def pullAndPush( self, cursor, currentRevision, increment, threshold, useCursorFile,
		sleepInterval, oneRevision, db, dbCursor ):
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
					'remotetitle': unescape( revision['title'] ),
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
					pushParameters['user'] = unescape( revision['user'] )
					pushParameters['userid'] = revision['userid']
				if 'commenthidden' in revision:
					pushParameters['deleted'] = pushParameters['deleted'] + 2
					pushParameters['summary'] = ''
				else:
					pushParameters['summary'] = unescape( revision['comment'] )
				if 'texthidden' in revision['slots']['main']:
					pushParameters['deleted'] = pushParameters['deleted'] + 1
					pushParameters['text'] = ''
					pushParameters['size'] = revision['size']
				else:
					pushParameters['text'] = unescape( revision['slots']['main']['*'] )
					pushParameters['size'] = len( pushParameters['text'] )
				pprint.pprint(pushParameters)
				#pushGen = pywikibot.data.api.Request(
				#	self.siteTest, parameters=pushParameters )
				#pushData = pushGen.submit()
				#pprint.pprint(pushData)
				#if pushData['edit']['result'] == 'Success':
					#if currentRevision > threshold:
				newRevTimestamp = revision['timestamp'][0:4]
				newRevTimestamp = newRevTimestamp + revision['timestamp'][5:7]
				newRevTimestamp = newRevTimestamp + revision['timestamp'][8:10]
				newRevTimestamp = newRevTimestamp + revision['timestamp'][11:13]
				newRevTimestamp = newRevTimestamp + revision['timestamp'][14:16]
				newRevTimestamp = newRevTimestamp + revision['timestamp'][17:19]
				sql = "INSERT INTO page(page_namespace, "
				sql = sql + "page_title, page_restrictions, page_is_new,"
				sql = sql + "page_random, page_touched, page_links_updated,"
				sql = sql + "page_latest, page_len, page_content_model) "
				sql = sql + "VALUES (1000, '" + str(revision['revid']) + "', '', 1,"
				#sql = sql + str(float(random.randint(1, 999999999999)/1000000000000)) + ","
				#sql = sql + "0." + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
				#sql = sql + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
				#sql = sql + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
				#sql = sql + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
				#sql = sql + random.randint(1,9) + random.randint(1,9) + ","
				sql = sql + "RAND(), "
				sql = sql + "20301231010203, 20301231010203, 0,"
				sql = sql + str( pushParameters['size'] ) + ","
				sql = sql + "'wikitext')"
				print (sql)
				try:
					dbCursor.execute(sql)
					db.commit()
				except TypeError as e:
					print (e)
					db.rollback()
					sys.exit()
				pageRowId = dbCursor.lastrowid
				print("last page row id:" + str(pageRowId))
				sql = "INSERT INTO text(old_text,old_flags) VALUES ('"
				sql = sql + MySQLdb.escape_string( pushParameters['text'].encode('utf-8') ) + "','')"
				try:
					dbCursor.execute(sql)
				except TypeError as e:
					print (e)
					db.rollback()
					sys.exit()
				textRowId = dbCursor.lastrowid
				#m = hashlib.md5()
				#m.update( unescape( data['text'] ) )
				#hash = hashlib.md5( unescape( data['text'] ) ).hexdigest()
				print("last text row id:" + str(textRowId))
				revision['title'] = revision['title'].replace(' ', '_')
				revMinorEdit = 0
				if 'minor' in revision:
					revMinorEdit = 1
				sql = "INSERT INTO revision(rev_page,rev_text_id,rev_comment,rev_user,rev_user_text,"
				sql = sql + "rev_timestamp, rev_minor_edit, rev_deleted, rev_len," # rev_parent_id omitted
				sql = sql + "rev_sha1, rev_content_model, rev_content_format, rev_remote_page,"
				sql = sql + "rev_remote_namespace, rev_remote_title, rev_remote_rev, rev_remote_user) "
				sql = sql + "VALUES ( " + str(pageRowId) + "," + str(textRowId) + ","
				sql = sql + "'" + MySQLdb.escape_string( pushParameters['summary'] ) + "', "
				sql = sql + "0, "
				sql = sql + "'" + MySQLdb.escape_string( pushParameters['user'].encode('utf-8') ) + "', "
				sql = sql + str(newRevTimestamp) + ", " + str(revMinorEdit) + ", "
				sql = sql + str(pushParameters['deleted']) + ", "
				sql = sql + str( pushParameters['size'] ) + ", '"
				#sql = sql + MySQLdb.escape_string( m.digest() ) + "','wikitext',"
				#sql = sql + MySQLdb.escape_string( hash ) + "','wikitext',"
				sql = sql + "','wikitext',"
				sql = sql + "'text/x-wiki'," + str(revision['pageid']) + ", " + str(revision['ns']) + ", '"
				sql = sql + MySQLdb.escape_string( revision['title'].encode('utf-8') ) + "', "
				sql = sql + str( revision['revid'] ) + ", " + str( pushParameters['userid'] )
				sql = sql + ")"
				print (sql)
				try:
					dbCursor.execute(sql)
				except TypeError as e:
					print (e)
					db.rollback()
					sys.exit()
				revRowId = dbCursor.lastrowid
				print("last rev row id:" + str(revRowId))
				sql = "UPDATE page SET page_latest=" + str(revRowId) + " WHERE page_id=" + str(pageRowId)
				try:
					dbCursor.execute(sql)
					db.commit()
				except TypeError as e:
					print (e)
					db.rollback()
					sys.exit()
				#sys.exit()
				currentRevision = revision['revid'] + increment
				cursorFilename = 'cursor' + str(cursor) + '.txt'
				if useCursorFile == True:
					f = open( cursorFilename, 'w')
					f.write( str( currentRevision ) + "\n" )
					f.close()
				#else:
				#	print ( 'Edit failure' )
				#	pprint.pprint(pushData['edit']['result'])
				#	sys.exit()
				if oneRevision == True:
					sys.exit()
		
siteTest = pywikibot.Site(code='en', fam='test2')
if not siteTest.logged_in():
    siteTest.login()
siteWikipedia = pywikibot.Site(code='en', fam='wikipedia')
# Defaults
cursor = -1
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
if cursor == -1:
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
db = MySQLdb.connect("localhost","admin","314159265","test2" )
# prepare a cursor object using cursor() method
dbCursor = db.cursor()
myTestScript.pullAndPush( cursor, currentRevision, increment, threshold, useCursorFile,
	sleepInterval, oneRevision, db, dbCursor )