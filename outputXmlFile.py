import sys
maxLines = 100
if len(sys.argv) > 1:
	fileName = sys.argv[1]
else:
	print ( 'Usage: python outputXmlFile.py [filename] [maxlines]' )
	sys.exit()
if len(sys.argv) > 2:
	maxLines = int(sys.argv[2])
file = open(fileName, 'r')
thisLine = 0
for line in file:
	print line,
	thisLine = thisLine + 1
	if thisLine > maxLines:
		sys.exit()