#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
import os, sys, shutil
import struct
from struct import *
import Image

my_module_version = "0.50"
my_module_name = "fonFileLib"


class FonHeader:
    maxEntriesInTableOfDetails = -1 # this is probably always the number of entries in table of details, but it won't work for the corrupted TAHOMA18.FON file
    maxGlyphWidth = -1          # in pixels
    maxGlyphHeight = -1         # in pixels
    graphicSegmentByteSize = -1 # Graphic segment byte size

    def __init__(self):
        return


class fonFile:
    m_header = FonHeader()

    simpleFontFileName = "GENERIC.FON"

    glyphDetailEntriesLst = []  # list of 5-value tuples. Tuple values are (X-offset, Y-offset, Width, Height, Offset in Graphics segment)
    glyphPixelData = None       # buffer of pixel data for glyphs

    def __init__(self):
        del self.glyphDetailEntriesLst[:]
        return

    def loadFonFile(self, fonBytesBuff, maxLength, fonFileName):
        self.simpleFontFileName =  fonFileName
        offsInFonFile = 0
		#
		# parse FON file fields for header
		#
        try:
            tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
            self.header().maxEntriesInTableOfDetails = tmpTuple[0]
            offsInFonFile += 4

            tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
            self.header().maxGlyphWidth = tmpTuple[0]
            offsInFonFile += 4

            tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
            self.header().maxGlyphHeight = tmpTuple[0]
            offsInFonFile += 4

            tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
            self.header().graphicSegmentByteSize = tmpTuple[0]
            offsInFonFile += 4

            print "FON Header Info: "
            print "Num of entries: %d\tGlyph max-Width: %d\tGlyph max-Height: %d\tGraphic Segment size %d" % (self.header().maxEntriesInTableOfDetails, self.header().maxGlyphWidth, self.header().maxGlyphHeight, self.header().graphicSegmentByteSize)
			#
			# Glyph details table (each entry is 5 unsigned integers == 5*4 = 20 bytes)
            # For most characters, their ASCII value + 1 is the index of their glyph's entry in the details table. The 0 entry of this table is reserved
			#
            #tmpXOffset, tmpYOffset, tmpWidth, tmpHeight, tmpDataOffset
            glyphEntryIndex = 0
            print "FON glyph details table: "
            for idx in range(0, self.header().maxEntriesInTableOfDetails):
                tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
                tmpXOffset = tmpTuple[0]
                offsInFonFile += 4

                tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
                tmpYOffset = tmpTuple[0]
                offsInFonFile += 4

                tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
                tmpWidth = tmpTuple[0]
                offsInFonFile += 4

                tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
                tmpHeight = tmpTuple[0]
                offsInFonFile += 4

                tmpTuple = struct.unpack_from('I', fonBytesBuff, offsInFonFile)  # unsigned integer 4 bytes
                tmpDataOffset = tmpTuple[0]
                offsInFonFile += 4

                print "Index: %d\txOffs: %d\tyOffs: %d\twidth: %d\theight: %d\tdataOffs: %d" % (glyphEntryIndex, tmpXOffset, tmpYOffset, tmpWidth, tmpHeight, tmpDataOffset)
                self.glyphDetailEntriesLst.append( ( tmpXOffset, tmpYOffset, tmpWidth, tmpHeight, tmpDataOffset) )
                glyphEntryIndex += 1

            self.glyphPixelData = fonBytesBuff[offsInFonFile:]
			# strings (all entries are null terminated)
			#  TODO +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
			## absStartOfIndexTable = 4
			#absStartOfOffsetTable = absStartOfIndexTable + (self.header().numOfTextResources * 4)
			#absStartOfStringTable = absStartOfOffsetTable + ((self.header().numOfTextResources+1) * 4)

			#print "buffer type " , type(fonBytesBuff) # it is str

			#for idx in range(0, self.header().numOfTextResources):
			#	currOffset = self.stringOffsets[idx] + absStartOfIndexTable
			#	# the buffer (fonBytesBuff) where we read the TRE file into, is "str" type but contains multiple null terminated strings
			#	# the solution here (to not get out of index errors when reading the null terminator points) is
			#	# to split the substring starting at the indicated offset each time, at the null character, and get the first string token.
			#	# This works ok.
			#	#
			#	allTextsFound = fonBytesBuff[currOffset:].split('\x00')
			#	# check "problematic" character cases:
			#	if  currOffset == 5982 or currOffset == 6050 or currOffset == 2827  or currOffset == 2880:
			#	 	print "Offs: %d\tFound String: %s" % ( currOffset,''.join(allTextsFound[0]) )
			#		 #print "Offs: %d\tFound String: %s" % ( currOffset,''.join(allTextsFound[0]) )
			#	(theId, stringOfIdx) = self.stringEntriesLst[idx]
			#	self.stringEntriesLst[idx] = (theId, ''.join(allTextsFound[0]))
			#	#print "ID: %d\tFound String: %s" % ( theId,''.join(allTextsFound[0]) )
            return True
        except:
            print "Loading failure!"
            raise
            return False

    def outputFonToPNG(self):
        targWidth = 0
        targHeight = 0
        paddingFromTopY = 2
        paddingBetweenGlyphsX = 2

        if len(self.glyphDetailEntriesLst) == 0 or len(self.glyphDetailEntriesLst) != self.header().maxEntriesInTableOfDetails:
            print "Error. Fon file load process did not complete correctly. Missing important data in structures. Cannot output image!"
            return

        realNumOfCharactersInImageSegment = 0
        if self.simpleFontFileName == 'TAHOMA18.FON': # deal with corrupted original 'TAHOMA18.FON' file
            realNumOfCharactersInImageSegment = 176
            print "SPECIAL CASE. WORKAROUND FOR CORRUPTED %s FILE. Only %d characters supported!" % (self.simpleFontFileName, realNumOfCharactersInImageSegment)
        else:
            realNumOfCharactersInImageSegment = self.header().maxEntriesInTableOfDetails

        # TODO asdf refine this code here. the dimensions calculation is very crude for now
        if self.header().maxGlyphWidth > 0 :
            targWidth = (self.header().maxGlyphWidth + paddingBetweenGlyphsX) * self.header().maxEntriesInTableOfDetails
        else:
            targWidth = 1080

        # TODO asdf refine this code here. the dimensions calculation is very crude for now
        if self.header().maxGlyphHeight > 0 :
            targHeight = self.header().maxGlyphHeight * 2
        else:
            targHeight = 480

        imTargetGameFont = Image.new("RGBA",(targWidth, targHeight), (0,0,0,0))
        print imTargetGameFont.getbands()
        # Now fill in the image segment
        # Fonts in image segment are stored in pixel colors from TOP to Bottom, Left to Right per GLYPH.
        # Each pixel is 16 bit (2 bytes). Highest bit seems to determine transparency (on/off flag).
        # There seem to be 5 bits per RGB channel and the value is the corresponding 8bit value (from the 24 bit pixel color) shifting out (right) the 3 LSBs
        # First font image is the special character (border of top row and left column) - color of font pixels should be "0x7FFF" for filled and "0x8000" for transparent

        for idx in range(0, realNumOfCharactersInImageSegment):
            # TODO check for size > 0 for self.glyphPixelData
            # TODO mark glyph OUTLINES? (optional by switch)
            (glyphXoffs, glyphYoffs, glyphWidth, glyphHeight, glyphDataOffs) = self.glyphDetailEntriesLst[idx]
            glyphDataOffs = glyphDataOffs * 2
            #print idx, glyphDataOffs
            currX = 0
            currY = 0
            for colorIdx in range(0, glyphWidth*glyphHeight):
                tmpTuple = struct.unpack_from('H', self.glyphPixelData, glyphDataOffs)  # unsigned short 2 bytes
                pixelColor = tmpTuple[0]
#                if pixelColor > 0x8000:
#                    print "WEIRD CASE" # NEVER HAPPENS - TRANSPARENCY IS ON/OFF. There's no grades of transparency
                rgbacolour = (0,0,0,0)
                if pixelColor == 0x8000:
                    rgbacolour = (0,0,0,0) # alpha: 0.0 fully transparent
                else:
                    tmp8bitR1 =  ( (pixelColor >> 10) ) << 3
                    tmp8bitG1 =  ( (pixelColor & 0x3ff) >> 5 ) << 3
                    tmp8bitB1 =  ( (pixelColor & 0x1f) ) << 3
                    rgbacolour = (tmp8bitR1,tmp8bitG1,tmp8bitB1, 255)   # alpha: 1.0 fully opaque
                    #rgbacolour = (255,255,255, 255)   # alpha: 1.0 fully opaque

                if currX == glyphWidth:
                    currX = 0
                    currY += 1
                imTargetGameFont.putpixel(( (idx * self.header().maxGlyphWidth + paddingBetweenGlyphsX ) + currX, paddingFromTopY + glyphYoffs + currY), rgbacolour)
                currX += 1
                glyphDataOffs += 2
        imTargetGameFont.save(os.path.join('.', self.simpleFontFileName + ".PNG"), "PNG")

    def header(self):
        return self.m_header
#
#
#
if __name__ == '__main__':
    #	 main()
    print "Running %s as main module" % (my_module_name)
    # assumes a file of name TAHOMA24.FON in same directory
    inFONFile = None
    #inFONFileName =  'TAHOMA24.FON'        # USED IN CREDIT END-TITLES and SCORERS BOARD AT POLICE STATION
    #inFONFileName =  'TAHOMA18.FON'        # USED IN CREDIT END-TITLES
    #inFONFileName =  '10PT.FON'            # BLADE RUNNER UNUSED FONT?
    inFONFileName =  'KIA6PT.FON'          # BLADE RUNNER MAIN FONT
    errorFound = False
    try:
        inFONFile = open(os.path.join('.',inFONFileName), 'rb')
    except:
        errorFound = True
        print "Unexpected error:", sys.exc_info()[0]
        raise
    if not errorFound:
        allOfFonFileInBuffer = inFONFile.read()
        fonFileInstance = fonFile()
        if (fonFileInstance.loadFonFile(allOfFonFileInBuffer, len(allOfFonFileInBuffer), inFONFileName)):
            print "FON file loaded successfully!"
            fonFileInstance.outputFonToPNG()
        else:
            print "Error while loading FON file!"
            inFONFile.close()
else:
    #debug
    #print "Running	 %s imported from another module" % (my_module_name)
    pass