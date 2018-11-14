import sys
import pprint
import pywikibot

class pushXmlFile:
	def __init__(self, test, fileName, soFar, maxLines, oneRevision ):
		self.siteTest = test
		self.soFar = soFar
		self.reachedSoFar = False
		self.fileName = fileName
		self.maxLines = maxLines
		self.oneRevision = oneRevision

	def parseXmlFile ( self ):		
		file = open(fileName, 'r')
		thisLine = 0
		data = { 'text': ''}
		dataTypes = [ 'title', 'ns', 'timestamp', 'username', 'ip', 'comment' ] # XML tags
		defaultData = { 'username': '', 'ip': '', 'text': '', 'deleted': 0, 'minor': False }
		modes = [ 'page', 'revision', 'contributor' ] # There are XML sub-tags for these
		thisMode = ''
		texting = False
		textTag = '<text xml:space="preserve">'
		for line in file:
			#print line,
			textStart = line.find( textTag )
			textClose = line.find( '</text>' )
			if texting == True or textStart != -1 or line.find('<text deleted="deleted" />') != -1:
				if line.find('<text deleted="deleted" />') != -1:
					data['deleted'] += 1
					continue
				texting = True # Begin processing potentially multiline text
				if textStart == -1: # Start at the beginning of the line
					textStart = 0
				if textClose == -1:
					textClose = len( line )
				data['text'] = data['text'] + line[textStart + len(textTag):textClose]
				if line.find( '</text>' ) != -1:
					texting = False # Prepare to process non-text stuff
					pushData ( data )
					pprint.pprint ( data )
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
						if dataType == 'id':
							dataType = thisMode + dataType
						data[dataType] = line[dataStart + len(dataType)+2:dataClose]
				if line.find( '<minor />' ) != -1:
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
		
def pushData( self, data ):
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
		'summary': data['comment'],
		#'sdtags': '|'.join(revision['tags']),
		'timestamp': data['timestamp'],
		'user': data['username'],
		'userid': data['contributorid'],
		'remoterev': data['revisionid'],
		'text': data['text']
	}
	if data['minor'] != '':
		pushParameters['minor'] = 'true'
	#if data['bot'] != '':
	#	pushParameters['bot'] = 'true'
	if self.reachedSoFar != True and self.soFar > 0:
		if self.soFar == data['revisionid']:
			self.reachedSoFar = True
		return
	pushGen = pywikibot.data.api.Request(
		self.siteTest, parameters=pushParameters )
	pushData = pushGen.submit()
	pprint.pprint(pushData)
	if pushData['edit']['result'] == 'Success':
		cursorFilename = 'cursor' + self.fileName + '.txt'
		f = open( cursorFilename, 'w')
		f.write( str(data['revisionid'] ) + "\n" )
		f.close()
	else:
		print ( 'Edit failure' )
		#pprint.pprint(pushData['edit']['result'])
		sys.exit()
	if oneRevision == True:
		sys.exit()

maxLines = 0 # Value of zero means there is no limit
soFar = 0
fileName = ''
#if os.path.isfile( cursorFilename ):
#	f = open( cursorFilename, 'r')
#	soFar = int( f.readline() )
for arg in sys.argv:
	if arg[0:9] == 'filename=':
		fileName = arg[9:]
	if arg[0:8] == 'maxlines=':
		maxLines = arg[8:]
	if arg[0:6] == '--sofar=':
		soFar = arg[6:]
	if arg[0:13] == '--onerevision':
		oneRevision = True
if len(sys.argv) < 2 or fileName == '':
	print ( 'Usage: python pushXmlfile.py [--filename=] [--maxlines=] [--sofar=] [--onerevision' )
	print ( 'Example: python pushXmlfile.py --filename=foo.xml' )
	sys.exit()
siteTest = pywikibot.Site(code='en', fam='test2')
if not siteTest.logged_in():
	siteTest.login()
myTestScript = pushXmlFile( siteTest, fileName, soFar, maxLines, oneRevision )
myTestScript.parseXmlFile ()