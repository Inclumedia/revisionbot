import sys
import pprint
import pywikibot
import MySQLdb
import json

from xml.sax.saxutils import unescape

class pushXmlFile:
	def __init__(self, test, fileName, soFar, maxLines, oneRevision ):
		self.siteTest = test
		self.soFar = soFar
		self.reachedSoFar = False
		self.fileName = fileName
		self.maxLines = maxLines
		self.oneRevision = oneRevision

	def parseXmlFile ( self ):
		# Open database connection
		rowId = 0
		db = MySQLdb.connect("localhost","admin","314159265","test2" )
		# prepare a cursor object using cursor() method
		cursor = db.cursor()
		#h= HTMLParser.HTMLParser()
		file = open(fileName, 'r')
		thisLine = 0
		data = { 'text': ''}
		dataTypes = [ 'title', 'ns', 'timestamp', 'username', 'ip', 'comment', 'id' ] # XML tags
		defaultData = { 'username': '', 'ip': '', 'comment': '', 'text': '',
			'deleted': 0, 'contributorid': 0, 'minor': False }
		modes = [ 'page', 'revision', 'contributor' ] # There are XML sub-tags for these
		thisMode = ''
		texting = False
		textTag = '<text xml:space="preserve"'
		for key, defaultDatum in defaultData.items():
			data[key] = defaultDatum
		for line in file:
			print line,
			textStart = line.find( textTag )
			textClose = line.find( '</text>' )
			if texting == True or textStart != -1 or line.find('<text deleted="deleted" />') != -1:
				if line.find('<text deleted="deleted" />') != -1:
					data['deleted'] += 1
				else:
					#print ( 'processing') 
					texting = True # Begin processing potentially multiline text
					if textStart == -1: # Start at the beginning of the line
						textStart = 0
					else:
						textStart = line.find( '>' ) + 1
					if textClose == -1:
						textClose = len( line )
					#data['text'] = data['text'] + h.unescape( line[textStart:textClose] )
					data['text'] = data['text'] + line[textStart:textClose]
				if line.find( '</text>' ) != -1 or line.find('<text deleted="deleted" />') != -1:
					texting = False # Prepare to process non-text stuff
					pprint.pprint ( data )
					rowId = rowId + 1
					self.pushData ( db, cursor, data, rowId )
					for key, defaultDatum in defaultData.items():
						# Return everything to defaults in preparation for the next record
						data[key] = defaultDatum
					continue
			else:
				for mode in modes:
					modeStart = line.find( '<' + mode + '>' )
					if ( modeStart != -1 ):
						thisMode = mode	
				for dataType in dataTypes:	
					dataStart = line.find( '<' + dataType + '>' )
					if ( dataStart != -1 ):
						dataClose = line.find( '</' + dataType + '>' )
						#print line[titleStart + 7:titleClose]
						fullDataType = dataType
						if dataType == 'id':
							fullDataType = thisMode + dataType
						data[fullDataType] = line[dataStart + len(dataType)+2:dataClose]
				if line.find( '<minor' ) != -1:
					data['minor'] = True
			thisLine = thisLine + 1
			if maxLines > 0 and thisLine > self.maxLines:
				sys.exit()
			if line.find( '<comment deleted="deleted" />') != -1:
				data['deleted'] += 2
				data['comment'] = ''
			if line.find( '<contributor deleted="deleted" />') != -1:
				data['deleted'] += 4
				data['username'] = ''
		
	def pushData( self, db, cursor, data, rowId ):
		#h= HTMLParser.HTMLParser()
		#undesirables = [ '-', ':', 'T', 'Z' ]
		#for undesirable in undesirables:
		#	data['timestamp'] = data['timestamp'].replace( undesirable, '' )
		if data['username'] == '':
			data['username'] = data['ip']
		pushParameters = {
			'action': 'edit',
			'title': 'Revision:' + data['revisionid'],
			'namespace': data['ns'],
			'remotetitle': data['title'],
			'page': data['pageid'],
			'token': self.siteTest.tokens['edit'],
			'summary': unescape( data['comment'] ),
			#'sdtags': '|'.join(revision['tags']),
			'timestamp': data['timestamp'],
			'deleted': data['deleted'],
			'user': data['username'],
			'userid': data['contributorid'],
			'remoterev': data['revisionid'],
			'text': unescape( data['text'] )
		}
		newRevTimestamp = data['timestamp'][0:4]
		newRevTimestamp = newRevTimestamp + data['timestamp'][5:7]
		newRevTimestamp = newRevTimestamp + data['timestamp'][8:10]
		newRevTimestamp = newRevTimestamp + data['timestamp'][11:13]
		newRevTimestamp = newRevTimestamp + data['timestamp'][14:16]
		newRevTimestamp = newRevTimestamp + data['timestamp'][17:19]
		print (data['timestamp'])
		print (newRevTimestamp)
		#sys.exit()
		revMinorEdit = 0
		if data['minor'] != False:
			pushParameters['minor'] = 'true'
			revMinorEdit = 1
		#if data['bot'] != '':
		#	pushParameters['bot'] = 'true'
		if self.reachedSoFar != True and self.soFar > 0:
			if self.soFar == data['revisionid']:
				self.reachedSoFar = True
			return
		rowId = rowId + 1
		#pushGen = pywikibot.data.api.Request(
		#	self.siteTest, parameters=pushParameters )
		#pushData = pushGen.submit()
		#pprint.pprint(pushData)
		#if pushData['edit']['result'] == 'Success':
		#print ( str(float(random.randint(1, 999999999999)/1000000000000) ) )
		#sys.exit()
		#sql = "SELECT from page WHERE 
		sql = "INSERT INTO page(page_id, page_namespace, "
		sql = sql + "page_title, page_restrictions, page_is_new,"
		sql = sql + "page_random, page_touched, page_links_updated,"
		sql = sql + "page_latest, page_len, page_content_model) "
		sql = sql + "VALUES ( " + str(rowId) + ", 1000, '" + data['revisionid'] + "', '', 1,"
		#sql = sql + str(float(random.randint(1, 999999999999)/1000000000000)) + ","
		#sql = sql + "0." + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
		#sql = sql + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
		#sql = sql + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
		#sql = sql + random.randint(1,9) + random.randint(1,9) + random.randint(1,9)
		#sql = sql + random.randint(1,9) + random.randint(1,9) + ","
		sql = sql + "RAND(), "
		sql = sql + "20301231010203, 20301231010203, " + str(rowId) + ","
		sql = sql + str( len(unescape( data['text']) ) ) + ","
		sql = sql + "'wikitext')"
		print (sql)
		try:
			cursor.execute(sql)
		except TypeError as e:
			print (e)
			db.rollback()
			sys.exit()
		#pageRowId = cursor.lastrowid
		#print("last page row id:" + str(pageRowId))
		sql = "INSERT INTO text(old_id,old_text,old_flags) VALUES (" + str(rowId) + ",'"
		sql = sql + MySQLdb.escape_string( unescape( data['text'] ) ) + "','')"
		try:
			cursor.execute(sql)
		except TypeError as e:
			print (e)
			db.rollback()
			sys.exit()
		#textRowId = cursor.lastrowid
		#m = hashlib.md5()
		#m.update( unescape( data['text'] ) )
		#hash = hashlib.md5( unescape( data['text'] ) ).hexdigest()
		#print("last text row id:" + str(textRowId))
		data['title'] = data['title'].replace(' ', '_')
		sql = "INSERT INTO revision(rev_id,rev_page,rev_text_id,rev_comment,rev_user,rev_user_text,"
		sql = sql + "rev_timestamp, rev_minor_edit, rev_deleted, rev_len," # rev_parent_id omitted
		sql = sql + "rev_sha1, rev_content_model, rev_content_format, rev_remote_page,"
		sql = sql + "rev_remote_namespace, rev_remote_title, rev_remote_rev, rev_remote_user) "
		sql = sql + "VALUES ( " + str(rowId) + "," + str(rowId) + "," + str(rowId) + ","
		sql = sql + "'" + MySQLdb.escape_string( unescape( data['comment'] ) ) + "', "
		sql = sql + "0, "
		sql = sql + "'" + MySQLdb.escape_string( unescape( data['username'] ) ) + "', "
		sql = sql + str(newRevTimestamp) + ", " + str(revMinorEdit) + ", " + str(data['deleted']) + ", "
		sql = sql + str( len( unescape( data['text'] ) ) ) + ", '"
		#sql = sql + MySQLdb.escape_string( m.digest() ) + "','wikitext',"
		#sql = sql + MySQLdb.escape_string( hash ) + "','wikitext',"
		sql = sql + "','wikitext',"
		sql = sql + "'text/x-wiki'," + str(data['pageid']) + ", " + str(data['ns']) + ", '"
		sql = sql + MySQLdb.escape_string( unescape( data['title'] ) ) + "', "
		sql = sql + str( data['revisionid'] ) + ", " + str( data['contributorid'] )
		sql = sql + ")"
		print (sql)
		try:
			cursor.execute(sql)
			db.commit()
		except TypeError as e:
			print (e)
			db.rollback()
			sys.exit()
		#revRowId = cursor.lastrowid
		#print("last rev row id:" + str(revRowId))
		#sql = "UPDATE page SET page_latest=" + str(revRowId) + " WHERE page_id=" + str(pageRowId)
		#try:
		#	cursor.execute(sql)
		#	db.commit()
		#except TypeError as e:
		#	print (e)
		#	db.rollback()
		#	sys.exit()
		#sys.exit()
		cursorFilename = 'cursor' + self.fileName + '.txt'
		#f = open( cursorFilename, 'w')
		#f.write( str(data['revisionid'] ) + "\n" )
		cursorData = {}
		cursorData['variables'] = []
		cursorData['variables'].append({
			'revisionId': str(data['revisionid']),
			'rowid': str(rowId)
		})
		#with open(cursorFilename, 'w') as outfile:
		#	json.dump(cursorData, outfile)
		#else:
		#	print ( 'Edit failure' )
			#pprint.pprint(pushData['edit']['result'])
		#	sys.exit()
		if oneRevision == True:
			sys.exit()

maxLines = 0 # Value of zero means there is no limit
soFar = 0
fileName = ''
oneRevision = False
#if os.path.isfile( cursorFilename ):
#	f = open( cursorFilename, 'r')
#	soFar = int( f.readline() )
for arg in sys.argv:
	if arg[0:11] == '--filename=':
		fileName = arg[11:]
	if arg[0:10] == '--maxlines=':
		maxLines = arg[10:]
	if arg[0:6] == '--sofar=':
		soFar = arg[6:]
	if arg[0:13] == '--onerevision':
		oneRevision = True
if len(sys.argv) < 2 or fileName == '':
	print ( fileName )
	print ( 'Usage: python pushXmlfile.py [--filename=] [--maxlines=] [--sofar=] [--onerevision' )
	print ( 'Example: python pushXmlfile.py --filename=foo.xml' )
	sys.exit()
siteTest = pywikibot.Site(code='en', fam='test2')
if not siteTest.logged_in():
	siteTest.login()
myTestScript = pushXmlFile( siteTest, fileName, soFar, maxLines, oneRevision )
myTestScript.parseXmlFile ()