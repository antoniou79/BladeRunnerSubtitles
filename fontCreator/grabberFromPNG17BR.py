#!/usr/bin/python
# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------------
# Name:        grabberFromPNG15BR
# Purpose:     Parse the character fonts from a PNG file in order to create a
#              FON file for the Westwood Blade Runner PC game.
#
# Author:      antoniou
#
# Created:     16-05-2018
# Copyright:   (c) antoniou 2018
# Licence:
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#-------------------------------------------------------------------------------

#
# Let's assume an Input image with only a row of all character glyphs (no double rows...)
# BLADE RUNNER:
# TODO: Re-Check the order of fonts in (in-game resource font files) TAHOMA18 (stored corrupted) and TAHOMA24 (in good condition).
# TODO: print a warning for mismatch of number of letters in encoding override (or internal) and detected fonts in ROW IMAGE (especially if we expect a double exclamation mark at the start - and we ignoring one of the two)
# TODO: maybe test greek subs too.
# TODO: A more detailed readme for this tool and how to use it
# TODO: enforce overrideEncoding.txt -- this tool should no longer work without one
# DONE: Letter fonts should be spaced by TAB when copied into GIMP or other app to create the image row of all character glyphs
# DONE: First character should be repeated in the ROW file (but taken into consideration once) in order to get the pixels for the TAB space between letters (left-start column to left-start column)
# DONE: Use the tab space pixels to calculate the KERNING for each letter (x offset)
# DONE: update the image segment size bytes in the header after having completed populating the image segment
# DONE: allow settin explicit kerning and width addon for cases like i and l characters
# DONE: entrée (boiled dog question) - has an e like goose liver pate --> TESTED
# DONE: Tested ok "si senor" from peruvian lady / insect dealer too!
# DONE: ability to manually set kerning (x-offset) for fonts by letter like a list in parameters or in overrideEncoding.txt }  i:1,j:-1,l:1  (no space or white line characters) - POSITIVE OR NEGATIVE VALUES BOTH ADMITTED
# DONE: a value of '-' for this means ignore
# DONE: ability to manually set extra width (additional columns at the end of glyph, with transparent color) for fonts by letter like a list in parameters or in overrideEncoding.txt }  i:1,j:2,l:1 - POSITIVE VALUES ONLY
# DONE: make space pixels (var spaceWidthInPixels) into an external param?

import os, sys, shutil
import Image
from struct import *
import re

class grabberFromPNG:
    origEncoding = 'windows-1252'
    defaultTargetLang = "greek"
    defaultTargetEncoding = 'windows-1253' #greek
    defaultTargetEncodingUnicode = unicode(defaultTargetEncoding, 'utf-8')

    targetEncoding = 'windows-1253'
    targetEncodingUnicode = unicode(targetEncoding, 'utf-8')

    overrideEncodingTextFile = u'overrideEncoding.txt'
    relPath = u'.'
    overrideEncodingFileRelPath = os.path.join(relPath,overrideEncodingTextFile)

    BR_GameID = 3
    BR_Desc = 'Blade Runner'
    BR_CodeName = 'BLADERUNNER'
    BR_DefaultFontFileName = 'SUBTLS_E.FON'

    defaultSpaceWidthInPixelsConst = 0x0007 #0x0008  #0x0006
    spaceWidthInPixels = defaultSpaceWidthInPixelsConst

    reconstructEntireFont = False # TODO: TRUE!!!
    minSpaceBetweenLettersInRowLeftToLeft =0
    minSpaceBetweenLettersInColumnTopToTop = 0
    kerningForFirstDummyFontLetter = 0
#    deductKerningPixels = 0

    targetFONFilename = BR_DefaultFontFileName
#    origFontFilename=""
    origFontPropertiesTxt = ""
#    imageOriginalPNG=""
    imageRowFilePNG=""
    copyFontFileName=""
    copyFontPropertiesTxt = ""
    copyPNGFileName=""

    lettersFound = 0
    listOfBaselines = []
    listOfWidths = []
    listOfHeights = [] # new for Blade Runner support
    listOfLetterBoxes = []
    startColOfPrevFontLetter = 0 # new for Blade Runner support
    tabSpaceWidth = 0
    startOfAllLettersIncludingTheExtraDoubleAndWithKern = 0
    maxAsciiValueInEncoding  = 0

    listOfXOffsets = [] # new for Blade Runner support
    listOfYOffsets = [] # new for Blade Runner support

    listOfExplicitKerning = []
    listOfWidthIncrements = []

    ##
    ## FOR INIT PURPOSES!!!!
    ##
    overrideFailed = True
    targetLangOrderAndListOfForeignLettersStrUnicode = None
    targetLangOrderAndListOfForeignLettersStr = None
    # Read from an override file if it exists. Filename should be overrideEncoding.txt (overrideEncodingTextFile)
    if os.access(overrideEncodingFileRelPath, os.F_OK) :
        ## debug
        #print "Override encoding file found: {0}.".format(overrideEncodingFileRelPath)
        overEncodFile = open(overrideEncodingFileRelPath, 'r')
        linesLst = overEncodFile.readlines()
        overEncodFile.close()
        if linesLst is None or len(linesLst) == 0:
            overrideFailed = True
        else:
            print "Override Encoding Info: "
            involvedTokensLst =[]
            del involvedTokensLst[:] # unneeded
            for readEncodLine in linesLst:
                tmplineTokens = re.findall("[^\t\n]+",readEncodLine )
                for x in tmplineTokens:
                    involvedTokensLst.append(x)
#                print involvedTokensLst
                #break #only read first line
            if len(involvedTokensLst) >= 2:

                try:
                    targetEncodingUnicode = unicode(involvedTokensLst[0], 'utf-8')
                    targetEncoding = unicode.encode("%s" % targetEncodingUnicode, origEncoding)
                    targetLangOrderAndListOfForeignLettersStrUnicode = unicode(involvedTokensLst[1], 'utf-8')
                    print targetLangOrderAndListOfForeignLettersStrUnicode
                    if(len(involvedTokensLst) >=3):
                        print "involved tokens [2] (Explicit Kerning):", involvedTokensLst[2]
                        if(involvedTokensLst[2] != '-'):
                            # split at comma, then split at ':' and store tuples of character and explicit kerning
                            explicitKerningTokenUnicode = unicode(involvedTokensLst[2], 'utf-8')
                            explicitKerningTokenStr = unicode.encode("%s" % explicitKerningTokenUnicode, targetEncoding)
                            tokensOfExplicitKerningTokenStrList = explicitKerningTokenStr.split(',')
                            for tokenX in tokensOfExplicitKerningTokenStrList:
                                tokensOfTupleList = tokenX.split(':')
                                listOfExplicitKerning.append((ord(tokensOfTupleList[0]), int(tokensOfTupleList[1])) )

                    print "Explicit Kern List: " , listOfExplicitKerning
                    if(len(involvedTokensLst) >=4):
                        print "involved tokens [3] (positive add to char width):", involvedTokensLst[3]
                        if(involvedTokensLst[3] != '-'):
                            # split at comma, then split at ':' and store tuples of character and explicit additional width - POSITIVE VALUES ONLY
                            explicitWidthIncrementTokenUnicode = unicode(involvedTokensLst[3], 'utf-8')
                            explicitWidthIncrementTokenStr =  unicode.encode("%s" % explicitWidthIncrementTokenUnicode, targetEncoding)
                            tokensOfWidthIncrementStrList = explicitWidthIncrementTokenStr.split(',')
                            for tokenX in tokensOfWidthIncrementStrList:
                                tokensOfTupleList = tokenX.split(':')
                                listOfWidthIncrements.append((ord(tokensOfTupleList[0]), int(tokensOfTupleList[1])))
                    print "Explicit Width Increment List: " , listOfWidthIncrements
                    overrideFailed = False
                except:
                    overrideFailed = True
            else:
                overrideFailed = True

    else:
        ## debug
        print "Override encoding file not found: {0}.".format(overrideEncodingFileRelPath)
        print "To override the default encoding {0} use an override encoding file with two tab separated entries: encoding (ascii) and characters-list. Convert to UTF-8 without BOM and save. For example:".format(defaultTargetEncoding)
        print "windows-1252\t!!\"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}"
        pass

    if overrideFailed:
        ## debug
        print "Override encoding file FAILED-1. Initializing for {0}...".format(defaultTargetLang)
#        targetEncoding = defaultTargetEncoding
#        targetEncodingUnicode = defaultTargetEncodingUnicode
#        targetLangOrderAndListOfForeignLettersStrUnicode = unicode(allOfGreekChars, 'utf-8')
#        #print targetLangOrderAndListOfForeignLettersStrUnicode
        sys.exit()  # terminate if override Failed (Blade Runner)

    try:
        targetLangOrderAndListOfForeignLettersStr = unicode.encode("%s" % targetLangOrderAndListOfForeignLettersStrUnicode, targetEncoding)
    except:
        ## debug
        print "Override encoding file FAILED-2. Initializing for {0}...".format(defaultTargetLang)
#        targetEncoding = defaultTargetEncoding
#        targetEncodingUnicode = defaultTargetEncodingUnicode
#        targetLangOrderAndListOfForeignLettersStrUnicode = unicode(allOfGreekChars, 'utf-8')
#        targetLangOrderAndListOfForeignLettersStr = unicode.encode("%s" % targetLangOrderAndListOfForeignLettersStrUnicode, targetEncoding)
#        #print targetLangOrderAndListOfForeignLettersStrUnicode
        sys.exit()  # terminate if override Failed (Blade Runner)

    targetLangOrderAndListOfForeignLetters = list(targetLangOrderAndListOfForeignLettersStr)
    print  targetLangOrderAndListOfForeignLetters, len(targetLangOrderAndListOfForeignLetters)     # new
    targetLangOrderAndListOfForeignLettersAsciiValues = [ord(i) for i in targetLangOrderAndListOfForeignLetters]
    print targetLangOrderAndListOfForeignLettersAsciiValues, len(targetLangOrderAndListOfForeignLettersAsciiValues)
    maxAsciiValueInEncoding = max(targetLangOrderAndListOfForeignLettersAsciiValues)

#    for charAsciiValue in targetLangOrderAndListOfForeignLetters:
#        print "Ord of chars: %d" % ord(charAsciiValue)

    ##
    ## END OF INIT CODE
    ##

#
# TODO: warning: assumes that there is a margin on top and bellow the letters
# (especially on top; if a letter starts from the first pixel row,
# it might not detect it!) <---to fix
#
    def __init__(self, pselectedEncoding=None):
        self.minSpaceBetweenLettersInRowLeftToLeft = 0
        self.minSpaceBetweenLettersInColumnTopToTop = 0
        self.kerningForFirstDummyFontLetter = 0
        self.spaceWidthInPixels = self.defaultSpaceWidthInPixelsConst
#        self.deductKerningPixels = 0
        self.reconstructEntireFont = False # TODO : True?
        #self.origFontFilename=porigFontFilename
        self.targetFONFilename = self.BR_DefaultFontFileName
        self.copyFontFileName = ""
        self.copyPNGFileName=""
        #self.imageOriginalPNG=pimageOriginalPNG
        self.imageRowFilePNG = ""
        self.baselineOffset = 0

        self.lettersFound = 0
        self.origFontPropertiesTxt = ""
        self.copyFontPropertiesTxt = ""
        self.cleanup() # for good practice (this should not be here, but it's here too due to quick/sloppy :) coding (TODO: fix it)
        #debug
        #self.DBinit() # TODO REMOVE?
        if pselectedEncoding == None:
            pselectedEncoding = self.targetEncoding

        self.selectedGameID = self.BR_GameID
        self.activeEncoding = pselectedEncoding
        self.lettersInOriginalFontFile = 0 #initialization

        # TODO: we should get from the DB the encoding and lettersString
        # and the Empty slots for the selected Game and Calculcate the rest of
        # the lists/dictionaries on the fly.
        # IF no lettersString or encoding has been defined...
        # then issue error? or continue with hardcoded
        # (insert to db as well and inform the GUI?)
        #self.calcFromDB() # TODO REMOVE?
        return


    def cleanup(self):
        self.lettersFound = 0
        self.startColOfPrevFontLetter = 0
        self.tabSpaceWidth = 0
        self.startOfAllLettersIncludingTheExtraDoubleAndWithKern = 0
        del self.listOfBaselines[:]
        del self.listOfWidths[:]
        del self.listOfHeights[:]
        del self.listOfLetterBoxes[:]
        del self.listOfXOffsets[:] # new for Blade Runner support
        del self.listOfYOffsets[:] # new for Blade Runner support
#        del self.listOfExplicitKerning[:] # don't clean these up
#        del self.listOfWidthIncrements[:] # don't clean these up

        self.origFontPropertiesTxt = ""
        self.copyFontPropertiesTxt = ""
        return

##
## SETTERS
##
    def setImageRowFilePNG(self, pimageRowFilePNG):
        self.imageRowFilePNG = pimageRowFilePNG
        return

    def setTargetFONFilename(self, pTargetFONFilename):
        self.targetFONFilename = pTargetFONFilename
        return

    def setMinSpaceBetweenLettersInRowLeftToLeft(self, pminSpaceBetweenLettersInRowLeftToLeft):
        self.minSpaceBetweenLettersInRowLeftToLeft = pminSpaceBetweenLettersInRowLeftToLeft
        return
    def setMinSpaceBetweenLettersInColumnTopToTop(self, pminSpaceBetweenLettersInColumnTopToTop):
        self.minSpaceBetweenLettersInColumnTopToTop = pminSpaceBetweenLettersInColumnTopToTop
        return

    def setKerningForFirstDummyFontLetter(self, pKerningForFirstDummyFontLetter):
        self.kerningForFirstDummyFontLetter = pKerningForFirstDummyFontLetter
        return

#    def setDeductKerningPixels(self, pDeductKerningPixels):
#        self.deductKerningPixels = pDeductKerningPixels
#        return

    def setSpaceWidthInPixels(self, pSpaceWidthInPixels):
        self.spaceWidthInPixels = pSpaceWidthInPixels
        return

##
## END OF SETTERS
##



    def parseImage(self,  loadedImag, imwidth, imheight, trimTopPixels=0, trimBottomPixels = 0, firstDoubleLetterIgnore = False):
        """ parsing input image and detect one character font per run, and deleting the detected character font after calculating its specs (this is done in-memory; we are not writing back to the file)
        """
        prevColStartForLetter = 0
        prevRowStartForLetter = 0
        startCol = 0
        startRow = 0
        endCol = 0
        endRow = 0
        for x in range(0, imwidth):      # for each column
            if startCol != 0:
                break
            for y in range(0, imheight):     # we search all rows (for each column)
                r1,g1,b1,a1 = loadedImag[x, y]
                if a1 != 0:  # if pixel not completely transparent -- this is not necessarily the *top* left pixel of a font letter though! -- the startRow is still to be determined.
    #                print loadedImag[x, y]
                    if prevColStartForLetter == 0:
                        prevColStartForLetter = x
                        prevRowStartForLetter = y
                        startCol = x
    #                    print "Letter found"
    #                    print "start col:%d" % startCol
    # #                    print "hypothe row:%d" % y
    #                    # starting from the first row of the row-image (to do optimize), we parse by rows to find the top point (row coordinate) of the character font
     #                   for y2 in range(0, y+1):
                        tmpSum = y + self.minSpaceBetweenLettersInColumnTopToTop
                        scanToRow = imheight          # - explicitly set this to the whole image height -- assumes only one row of character fonts
                        if tmpSum < imheight:      # TODO: WAS scanToRow < imheight but this doesn't get executed anymore due to explicitly setting scanToRow to imheight (assuming only one row of character fonts)
                                                     # DONE: NEW changed check to if tmpSum < imgheight which makes more sense
                            scanToRow = tmpSum
                        for y2 in range(0, scanToRow):         # a loop to find the startRow  - Check by row (starting from the top of the image and the left column of the letter)
                            if startRow != 0:
                                break
                            tmpSum = startCol + self.minSpaceBetweenLettersInRowLeftToLeft
                            scanToCol = imwidth
                            if tmpSum < imwidth:
                                scanToCol = tmpSum
                            #print (startCol, scanToCol)
                            for x2 in range(startCol, scanToCol): # check all columns (for each row)
                                #print loadedImag[x2, y2]
                                r2,g2,b2,a2 = loadedImag[x2, y2]
                                if a2 != 0 and startRow == 0:
                                    startRow = y2 + trimTopPixels
    #                                print "start row: %d" % startRow
                                    break
        if startCol > 0 and startRow > 0:          # WARNING: TODO NOTE: SO NEVER HAVE AN INPUT IMAGE WHERE THE FONT CHARACTERS ARE TOUCHING THE TOP OF THE IMAGE WITH NO EMPTY SPACE WHATSOEVER
            tmpSum = startRow + self.minSpaceBetweenLettersInColumnTopToTop
            scanToRow = imheight
            if tmpSum < imheight:
               scanToRow = tmpSum
            tmpSum = startCol + self.minSpaceBetweenLettersInRowLeftToLeft
            scanToCol = imwidth
            if tmpSum < imwidth:
               scanToCol = tmpSum
            for y in range(startRow, scanToRow):        # now check per row (we go through all theoritical rows, no breaks)-- we want to find the bottom row
                for x in range(startCol, scanToCol):    # check the columns for each row
                    r1,g1,b1,a1 = loadedImag[x, y]
                    if a1 != 0:
                        endRow = y
            if endRow > 0:
                endRow = endRow - trimBottomPixels
    #        print "end row:% d" %endRow

        if startCol > 0 and startRow > 0 and endRow > 0:
            tmpSum = startCol + self.minSpaceBetweenLettersInRowLeftToLeft
            scanToCol = imwidth
            if tmpSum < imwidth:
               scanToCol = tmpSum
            for x in range(startCol, scanToCol):    # now check per column (we go through all theoritical columns, no breaks) -- we want to find the bottom column
                for y in range(startRow, endRow+1): # check the rows for each column
                    r1,g1,b1,a1 = loadedImag[x, y]
                    #print  loadedImag[x, y]
                    if a1 != 0:
                        endCol = x
    #        print "end col:% d" %endCol
        if startCol > 0 and startRow > 0 and endRow > 0 and endCol > 0:
            # append deducted baseline
            #
            if firstDoubleLetterIgnore == True:
                self.startOfAllLettersIncludingTheExtraDoubleAndWithKern = startCol - self.kerningForFirstDummyFontLetter
            else:                             # firstDoubleLetterIgnore == False
                if self.tabSpaceWidth == 0:
                    #print "start startPre", startCol, self.startColOfPrevFontLetter
                    self.tabSpaceWidth = startCol - self.startColOfPrevFontLetter
                    print "Tab Space Width detected: %d " % (self.tabSpaceWidth)
                # new if -- dont' use else here, to include the case of when we first detected the tab space width
                if self.tabSpaceWidth > 0:
                    self.listOfXOffsets.append(startCol - (self.startOfAllLettersIncludingTheExtraDoubleAndWithKern + (self.lettersFound + 1) * self.tabSpaceWidth) ) #  + self.deductKerningPixels )
                    #print "xOffSet", startCol - (self.startOfAllLettersIncludingTheExtraDoubleAndWithKern + (self.lettersFound + 1) * self.tabSpaceWidth)
                self.listOfBaselines.append(endRow)
                self.listOfWidths.append(endCol-startCol + 1) # includes the last col (TODO this was without the +1 for MI:SE translator -- possible bug? did we compensate?)
                self.listOfHeights.append(endRow - startRow + 1) # +1 includes the last row
                self.listOfLetterBoxes.append((startCol, startRow, endCol, endRow))

            self.startColOfPrevFontLetter = startCol      #update for next pass
            #delete the letter - even in the case of ignoring the first double letter
            for x in range(startCol, endCol+1):
                for y in range(startRow - trimTopPixels, endRow+1 + trimBottomPixels):
                   loadedImag[x, y] = 0, 0, 0, 0
            return 0
        else: return -1
#
#
#
    def generateModFiles(self, customBaselineOffs):
        """ Generate extended png and font files (work on copies, not the originals). Return values: 0 no errors, -1 output font file has alrady new letters, -2 no fonts found in png (TODO: more error cases)
        """
        #
        # When a customBaselineOffs is set, we should expand the space for the letter (otherwise it will be overflown in the next line or truncated (outside the png)
        # We can't expand the space for the letter downwards, because the engine will (com)press the new height to fit its expected and it will look bad.
        # NO THAT WON'T WORK--> The font will remain in the wrong place: Should we  CUT from the top and hope that we don't trunctate!? Keeping the resulting height equal to the expected one?
        # MAYBE: Do not alter the baseline of the original file, but the detected (popular) one of the line file!!!
        retVal = 0
        totalFontLetters = 0
        importedNumOfLetters = 0
        errMsg = ""
        errorFound = False
        im = None
        pix = None
        pixReloaded = None
        #
        # CONSTANTS
        #
        origGameFontDiakenoHeight = 0
        interLetterSpacingInPNG = 4
        origGameFontSizeEqBaseLine = 0
        # offset for start of PNG index table
#        firstTableLineOffset = self.PNG_TABLE_STARTLINE_OFFSET
        lettersInOriginalFontFile = self.lettersInOriginalFontFile
        #
        # detection of origGameFontSizeEqBaseLine
        #
        #origGameFontSizeEqBaseLine = self.findDetectedBaseline() ## NEW BR REMOVED
        self.cleanup() # necessary after detection of baseline, because it fills up some of the  lists used in the following!

##        self.origFontPropertiesTxt = self.getImagePropertiesInfo(True) # "%dx%dx%s" % (im.size[0],im.size[1], im.mode) # NEW REMOVED
#        print "WEEEE::: ", self.imageOriginalPNG, im.format, "%dx%d" % im.size, im.mode
#        print "BASELINE DETECTED:%d " % origGameFontSizeEqBaseLine

        #
        # OPEN THE IMAGE WITH THE ROW OF CHARACTER FONTS TO BE IMPORTED
        #
        if os.access(self.imageRowFilePNG, os.F_OK) :
            try:
                im = Image.open(self.imageRowFilePNG)
            except:
                errMsg = "No letters were found in input png!"
                print errMsg
                retVal = -2
                errorFound = True
        else:
            errMsg = "No letters were found in input png!"
            print errMsg
            retVal = -2
            errorFound = True
        if not errorFound:
            #debug
            #print self.imageRowFilePNG, im.format, "%dx%d" % im.size, im.mode
            w1, h1 = im.size
            trimTopPixels = 0
            trimBottomPixels = 0
            italicsMode = False   # will be set to true only if the prefix of the row file is itcrp_ or it_ in order to activate some extra settings for kerning and letter width!
            # TODO the note about special handling of row PNG files with it_ or itcrp_ prefix, should be moved to the documentation
            # TODO the special settings for handling italic native letters should be in the settings(?)
            filepathSplitTbl = os.path.split(self.imageRowFilePNG)
            sFilenameOnlyImageRowFilePNG = filepathSplitTbl[1]

            if sFilenameOnlyImageRowFilePNG.startswith("itcrp_") or sFilenameOnlyImageRowFilePNG.startswith("it_"):
                italicsMode = True

            if sFilenameOnlyImageRowFilePNG.startswith("itcrp_"):
                trimTopPixels = 1
                trimBottomPixels = 1
                print "Will trim upper line by %d pixels and bottom line by %d pixels" % (trimTopPixels, trimBottomPixels)
            pix = im.load()
            # pix argument is mutable (will be changed in the parseImage body)
            if self.parseImage(pix, w1, h1, trimTopPixels, trimBottomPixels, True) == 0:    #first run, just get the start column, ignore the letter - don't store it . We need this for the tab space width calculation and eventually the kerning calc of the letters
                # after the first call, we got an update on self.startColOfPrevFontLetter using the dummy double firstg letter font
                while self.parseImage(pix, w1, h1, trimTopPixels, trimBottomPixels) == 0:
                    self.lettersFound = self.lettersFound + 1 # == 0 means one character font was detected so +1 to the counter
        #    print self.listOfBaselines
            #debug
            print "Font Letters Detected (not including the first double): %d" % (self.lettersFound)
            if (self.lettersFound ) > 0 :
                print "widths: ", self.listOfWidths[0:]
                print "Plain x offsets:"
                print zip(self.targetLangOrderAndListOfForeignLettersAsciiValues[1:], self.listOfXOffsets)
#                # normalize x offsets
#                minXoffset = min(self.listOfXOffsets)
#                if(minXoffset < 0):
#                    addNormalizer = minXoffset * (-1)
#                    self.listOfXOffsets = [ x + addNormalizer  for x in self.listOfXOffsets]
#                print "Normalized x offsets: "
#                print self.listOfXOffsets
                # calculate y offsets
                (listOfStartCols, listOfStartRows, listOfEndCols, listOfEndRows) = zip(* self.listOfLetterBoxes)
                minTopRow = min(listOfStartRows)
                self.listOfYOffsets = [ x - minTopRow for x in listOfStartRows]
                print "Y offsets: "
                print self.listOfYOffsets
                #
                #
                # # actually explicit Width setting could affect this so ASDF TODO calc a new list here with final widths and get the max on that list!
                #
                listOfCalcWidths = []
                kIncIndx = 1
                for tmpWidth in self.listOfWidths:
                    explicitWidthIncrementVal = 0
                    if len(self.listOfWidthIncrements ) > 0:
                        tmpOrd = self.targetLangOrderAndListOfForeignLettersAsciiValues[kIncIndx]
                        keysOfWidthIncrements, valuesOfWidthIncrements = (zip(*self.listOfWidthIncrements))
                        if tmpOrd in keysOfWidthIncrements:
                            print "Explicit width increment for %d: %d" % (tmpOrd, valuesOfWidthIncrements[keysOfWidthIncrements.index(tmpOrd)])
                            explicitWidthIncrementVal = valuesOfWidthIncrements[keysOfWidthIncrements.index(tmpOrd)]
                            listOfCalcWidths.append(tmpWidth + explicitWidthIncrementVal )
                    if explicitWidthIncrementVal == 0:
                        listOfCalcWidths.append(tmpWidth)
                    kIncIndx = kIncIndx + 1
                #maxFontWidth =  max(self.listOfWidths)
                maxFontWidth =  max(listOfCalcWidths)
                maxFontHeight =  max(self.listOfHeights)
                print "Max Width, Max Height (not necessarily for the same character font): %d, %d" % (maxFontWidth, maxFontHeight)
                targetFontFile = None
                try:
                    targetFontFile = open(self.targetFONFilename, 'wb')
                except:
                    errorFound = True
                if not errorFound:
                # reopen the image with our Fonts because we deleted the letters in the in-mem copy
                    im = None
                    if os.access(self.imageRowFilePNG, os.F_OK) :
                        try:
                            im = Image.open(self.imageRowFilePNG)
                        except:
                            errorFound = True
                    else:
                        errorFound = True
                    if not errorFound:
                        pixReloaded = None
                        pixReloaded = im.load()

                        # first 4 bytes are the max ascii char value supported (it's basically the number of entries in the character index table)
                        # next 4 bytes are max font char width  (pixels)
                        # next 4 bytes are max font char height (pixels)
                        # next 4 bytes give the size of the graphic segment for the font characters (this size is in word units, so it needs *2 to get the byte size)
                        #               this size should be updated at the end (after filling the file with all font image data)
                        #
                        # pack 'I' unsigned int
                        print "NumberOfEntriesInFontTabl", (self.maxAsciiValueInEncoding + 1 + 1)
                        numberOfEntriesInFontTable = self.maxAsciiValueInEncoding + 1 + 1  # 0x0100 # This is actually the max ascii value + plus one (1) to get the font index value + plus another one (1) to get the count (since we have zero based indices)
                                                            # TODO ??? could be more than this if we need to keep other characters (not in our codeset) and expand the ascii table and offset the new characters
                        numberOfEntriesInFontTableInFile = pack('I', numberOfEntriesInFontTable )
                        targetFontFile.write(numberOfEntriesInFontTableInFile)
                        maxFontWidthPixelsToWrite = pack('I', maxFontWidth)
                        targetFontFile.write(maxFontWidthPixelsToWrite)
                        maxFontHeightPixelsToWrite = pack('I', maxFontHeight)
                        targetFontFile.write(maxFontHeightPixelsToWrite)
                        fontImagesSegmentSize = pack('I', 0x0000) #  - to be updated at the end!
                        targetFontFile.write(fontImagesSegmentSize)

                        startOfImageSegmentAbs = 0x10 + 20 * numberOfEntriesInFontTable # header is 0x10 bytes. Then table of  20 bytes *   numberOfEntriesInFontTable and then the data.
                        lastImageSegmentOffset = 0
    #                    targetFontFile.close() # don't close here
                        #
                        # Fonts index table - properties and offset in image segment
                        # TODO - REVISE WHEN FINISHED WITH COMPLETE TRANSCRIPT for special glyphs
                        # So far additional required characters (not included in the standard ASCII (127 chars) are:
                        # the spanish i (put it in ascii value 0xA2 (162), font index 0xA3)? todo verify -- actual ascii value in codepage 1252 is 0xED
                        # the spanish n (put it in ascii value 0xA5 (165), font index 0xA6)? todo verify -- actual ascii value in codepage 1252 is 0xF1
                        # DONE we also need special fonts for liver  pâté
                        #                                           a actual ascii value is 0xE2 in codepage 1252 -- put it in ascii value 0xA6 (165) -- font index 0xA7
                        #                                           e actual ascii value is 0xE9 in codepage 1252 -- put it in ascii value 0xA7 (166) -- font index 0xA8
                        # In the row png font, the letter fonts should be the actual character fonts (spanish n, i etc)
                        #               but in the overrideEncoding.txt we need the corresponding ascii characters for the particular codepage of the text (eg here the greek windows-1253)
                        #
                        # NOTE! WARNING: We need to add the corresponding ascii characters for our codepage (eg for Windows 1253 the characters with value 0xA2 and 0xA5 which are not the spanish characters but will act as delegates for them)
                        # the greek Ά (alpha tonoumeno) character has ascii value 0xA2 (162) (in codeset Windows 1253) so conflict with i in in-game Tahoma -- put it in 0xA3 (font index 0xA4)
                        # We should fill all unused characters with "space" placeholder. Probably all of them should also point to the same area (second block) of the image segment too.
                        # First block of the image area (font index = 0) is reserved and should be the "border" gamma-like character.
                        #
                        # Kerning of the first letter font is '1' for Tahoma18 (when shadowed from every side (the left side shadow reduces the kerning), otherwise it would be 2) -- TODO for now this should be a launch parameter
                        # Y offset should be calculated from the top row of the heighest font
                        kIncIndx = 0
                        for i in range(0, numberOfEntriesInFontTable):  # blocks of 20 bytes
                            # 20 byte block
                            # 4 bytes x offset (from what ref point? is this for kerning ) - CAN THIS BE NEGATIVE?
                            # 4 bytes y offset (from what ref point? is this for the baseline?) - CAN THIS BE NEGATIVE?
                            # 4 bytes char width
                            # 4 bytes char height
                            # 4 bytes offset in image segment (units in words (2 bytes))

                            # TODO add all standard ascii characters in the ROW IMAGE before the additional required spanish and then GREEK alphabet characters --
                            #                                           -- greek Ά should be at its proper place (between spanish i and spanish n).
                            # TODO check possible support issues for ώ greek character
                            if i == 0:
                                # the first entry is a special font character of max width and max height with a horizontal line across the top-most row and a vertical line across the left-most column
                                tmpXOffsetToWrite = pack('I', 0x0000)
                                targetFontFile.write(tmpXOffsetToWrite)
                                tmpYOffsetToWrite = pack('I', 0x0000)
                                targetFontFile.write(tmpYOffsetToWrite)
                                tmpWidthToWrite = pack('I', maxFontWidth)
                                targetFontFile.write(tmpWidthToWrite)
                                tmpHeightToWrite = pack('I', maxFontHeight)
                                targetFontFile.write(tmpHeightToWrite)
                                tmpDataOffsetToWrite = pack('I', 0x0000) # start of image segment means 0 offset
                                targetFontFile.write(tmpDataOffsetToWrite)
                                # TODO maybe conform more with game's format: Eg Tahoma24.fon (native game resource) does not always point to the second character font offset for dummy entries, but to the latest offset and only additionally sets the x-offset property (all others are 0) - eg look for 0x74c9 offsets (byte sequence 0xc9 0x74)
                                dummyCharFontImageConstOffset = maxFontWidth * maxFontHeight; # const. actual offset in bytes is twice that. This counts in words (2-bytes)  - This points to the first valid entry but with properties that make it translate as a space or dummy(?)
                                lastImageSegmentOffset = maxFontWidth * maxFontHeight; # actual offset in bytes is twice that. This counts in words (2-bytes)
                            else:
                                if (i-1) in self.targetLangOrderAndListOfForeignLettersAsciiValues:
                                    # then this is an actual entry
                                    #print i, ": actual entry index of ascii char", (i-1)," width:", self.listOfWidths[kIncIndx]
                                    #print "Self explicit kerning list: " , self.listOfExplicitKerning
                                    foundExplicitKern = False
                                    foundExplicitWidthIncrement = False
                                    if len(self.listOfExplicitKerning ) > 0:
                                        keysOfExplicitKerning, valuesOfExplicitKerning = (zip(*self.listOfExplicitKerning))
                                        if (i - 1) in keysOfExplicitKerning:
                                            print "Explicit kerning for %d " % (i-1)
                                            foundExplicitKern = True
                                            tmpXOffsetToWrite = pack('i', valuesOfExplicitKerning[keysOfExplicitKerning.index(i-1)]) # explicit X offset

                                    if foundExplicitKern == False:
                                        tmpXOffsetToWrite = pack('i', self.listOfXOffsets[kIncIndx]) # x offset - from left         # TODO check if ok. Changed to signed int since it can be negative sometimes!
                                    targetFontFile.write(tmpXOffsetToWrite)
                                    tmpYOffsetToWrite = pack('I', self.listOfYOffsets[kIncIndx])   # y offset from topmost row
                                    targetFontFile.write(tmpYOffsetToWrite)

                                    widthCalculatedValue = 0
                                    if len(self.listOfWidthIncrements ) > 0:
                                        keysOfWidthIncrements, valuesOfWidthIncrements = (zip(*self.listOfWidthIncrements))
                                        if (i - 1) in keysOfWidthIncrements:
                                            print "Explicit width increment for %d " % (i-1)
                                            foundExplicitWidthIncrement = True
                                            widthCalculatedValue = self.listOfWidths[kIncIndx] + valuesOfWidthIncrements[keysOfWidthIncrements.index(i-1)]
                                            tmpWidthToWrite = pack('I', widthCalculatedValue ) # explicit width increment

                                    if foundExplicitWidthIncrement == False:
                                        widthCalculatedValue = self.listOfWidths[kIncIndx]
                                        tmpWidthToWrite = pack('I', widthCalculatedValue )
                                    targetFontFile.write(tmpWidthToWrite)
                                    tmpHeightToWrite = pack('I', self.listOfHeights[kIncIndx])
                                    targetFontFile.write(tmpHeightToWrite)
                                    tmpDataOffsetToWrite = pack('I', lastImageSegmentOffset) #
                                    targetFontFile.write(tmpDataOffsetToWrite)
                                    lastImageSegmentOffset = lastImageSegmentOffset + widthCalculatedValue * self.listOfHeights[kIncIndx]
                                    kIncIndx = kIncIndx + 1 # increases only for valid characters
                                else:
                                    #
                                    #print i, ": phony entry"
                                    # TODO in-game resource fonts don't point all to the first entry as dummy but to the last valid entry encountered
                                    tmpXOffsetToWrite = pack('I', 0x0000) # 0 x offset
                                    targetFontFile.write(tmpXOffsetToWrite)
                                    tmpYOffsetToWrite = pack('I', 0x0000)   # 0 y offset
                                    targetFontFile.write(tmpYOffsetToWrite)
                                    tmpWidthToWrite = pack('I', self.spaceWidthInPixels) # font width set for some pixels of space # TODO ASDF maybe make this a parameter to be set at launch!
                                    targetFontFile.write(tmpWidthToWrite)
                                    tmpHeightToWrite = pack('I', 0x0000)
                                    targetFontFile.write(tmpHeightToWrite)
                                    tmpDataOffsetToWrite = pack('I', dummyCharFontImageConstOffset) #
                                    targetFontFile.write(tmpDataOffsetToWrite)
                        # end of for loop over all possible ascii values contained in the fon file
                        #
                        #
                        # Now fill in the image segment
                        # Fonts are written from TOP to Bottom, Left to Right. Each pixel is 16 bit (2 bytes). Highest bit seems to determine transparency (on/off flag).
                        #
                        # There seem to be 5 bits per RGB channel and the value is the corresponding 8bit value (from the 24 bit pixel color) shifting out (right) the 3 LSBs
                        # NOTE: Since we can't have transparency at channel level, it's best to have the input PNG not have transparent colored pixels (in Gimp merge the font layers, foreground and shadow and then from Layer settings set transparency threshold to 0 for that layer)- keep the background transparent!
                        #
                        # First font image is the special character (border of top row and left column) - color of font pixels should be "0x7FFF" for filled and "0x8000" for transparent
                        #
                        #
                        # Then follow up with the image parts for each letter!
                        #
                        #
                        #
                        # START of First special character image segment
                        #
                        for i in range(0, maxFontWidth * maxFontHeight):
                            if(i < maxFontWidth or i % maxFontWidth == 0):
                                tmpPixelColorRGB555ToWrite = pack('H', 0x7FFF) #unsigned short - 2 bytes
                                targetFontFile.write(tmpPixelColorRGB555ToWrite)
                            else:
                                tmpPixelColorRGB555ToWrite = pack('H', 0x8000)
                                targetFontFile.write(tmpPixelColorRGB555ToWrite) # unsigned short - 2 bytes
                        #
                        # END of First special character image segment
                        #
                        #
                        # Start rest of the font characters image segments
                        #
                        #

                        #
                        #   TODO ASDF if we have a character with explicit width increment (y) we should add columns of transparent colored pixels at the end (so since this is done by row, we should add y number of transparent pixels at the end of each row)
                        kIncIndx = 1 # start after the first glyph (which is DOUBLE)
                        for (c_startCol, c_startRow, c_endCol, c_endRow) in self.listOfLetterBoxes[0:]:
                            print (c_startCol, c_startRow, c_endCol, c_endRow),'for letter ', self.targetLangOrderAndListOfForeignLettersAsciiValues[kIncIndx]
                            explicitWidthIncrementVal = 0
                            if len(self.listOfWidthIncrements ) > 0:
                                tmpOrd = self.targetLangOrderAndListOfForeignLettersAsciiValues[kIncIndx]
                                keysOfWidthIncrements, valuesOfWidthIncrements = (zip(*self.listOfWidthIncrements))
                                if tmpOrd in keysOfWidthIncrements:
                                    print "Explicit width increment for %d: %d" % (tmpOrd, valuesOfWidthIncrements[keysOfWidthIncrements.index(tmpOrd)])
                                    explicitWidthIncrementVal = valuesOfWidthIncrements[keysOfWidthIncrements.index(tmpOrd)]


                            for tmpRowCur in range(c_startRow, c_endRow + 1):
                                for tmpColCur in range(c_startCol, c_endCol +1):
                                    #print (tmpRowCur, tmpColCur)
                                    r1,g1,b1,a1 = pixReloaded[tmpColCur, tmpRowCur] # Index col first, row second for image pixel array. TODO asdf this pix has been modified. All pixels would be transparent? - load image again?
                                    if(a1 == 0):
#                                        print "with alpha 8bit:", (r1, g1, b1, a1)
                                        #make completely transparent - write 0x8000
                                        tmpPixelColorRGB555ToWrite = pack('H', 0x8000)
                                        targetFontFile.write(tmpPixelColorRGB555ToWrite) # unsigned short - 2 bytes
                                    else:     # alpha should be 255 here really.
                                        #print "8bit:", (r1, g1, b1)
                                        tmp5bitR1 = (r1 >> 3) & 0x1f
                                        tmp5bitG1 = (g1 >> 3) & 0x1f
                                        tmp5bitB1 = (b1 >> 3) & 0x1f
                                        #print "5bit:", (tmp5bitR1, tmp5bitG1, tmp5bitB1)
                                        tmpPixelColorConvertedToRGB555 = (tmp5bitR1 << 10) | (tmp5bitG1 << 5) | (tmp5bitB1)
                                        #print "16bit:", tmpPixelColorConvertedToRGB555
                                        tmpPixelColorRGB555ToWrite = pack('H', tmpPixelColorConvertedToRGB555)
                                        targetFontFile.write(tmpPixelColorRGB555ToWrite) # unsigned short - 2 bytes
                                    if (tmpColCur == c_endCol and explicitWidthIncrementVal > 0):
                                        for tmpExtraColCur in range (0, explicitWidthIncrementVal):
                                            #make completely transparent - write 0x8000
                                            tmpPixelColorRGB555ToWrite = pack('H', 0x8000)
                                            targetFontFile.write(tmpPixelColorRGB555ToWrite) # unsigned short - 2 bytes
                            kIncIndx = kIncIndx + 1 # finally increase the kIncIndx for next glyph

                        #
                        # End rest of the font characters image segments
                        #
                        targetFontFile.close()
                        #
                        # Re -open and write the image segment
                        #
                        targetFontFile = None
                        try:
                            targetFontFile = open(self.targetFONFilename, 'r+b')
                        except:
                            errorFound = True
                        if not errorFound:
                            targetFontFile.seek(0x0C)     # position to write imageSegmentSize
                            tmpImageSegmentToWrite = pack('I', lastImageSegmentOffset)
                            targetFontFile.write(tmpImageSegmentToWrite)
                            targetFontFile.close()

            else: ## if (self.lettersFound ) <= 0
                errMsg = "No letters were found in input png!"
                print errMsg
                retVal = -2
        return (retVal, errMsg, origGameFontSizeEqBaseLine, totalFontLetters, importedNumOfLetters)


#
#
# ########################
# main
# sys.argv[1] filename of our png with row of fonts in same directory
# sys.argv[2] TMPTargetFONfilename
# sys.argv[3] TMPminSpaceBetweenLettersInRowLeftToLeft
# sys.argv[4] TMPminSpaceBetweenLettersInColumnTopToTop
# sys.argv[5] TMPkerningForFirstDummyFontLetter
# sys.argv[6] TMPSpaceWidthInPixels
#
# #########################
#
if __name__ == '__main__':
#    main()
    print "Usage: grabberFromPNG imageRowPNGFilename targetFONfilename minSpaceBetweenLettersInRowLeftToLeft minSpaceBetweenLettersInColumnTopToTop kerningForFirstDummyFontLetter whiteSpaceWidthInPixels" # deductKerningPixels"
    if len(sys.argv) == 7:
#        TMPreconstructEntireFont = False if (int(sys.argv[6]) == 0) else True
#        TMPreconstructEntireFont = True #hardcoded to true for Blade Runner
        TMPimageRowFilePNG = sys.argv[1]
        TMPTargetFONfilename = sys.argv[2]
        TMPminSpaceBetweenLettersInRowLeftToLeft = int(sys.argv[3])
        TMPminSpaceBetweenLettersInColumnTopToTop = int(sys.argv[4])
        TMPkerningForFirstDummyFontLetter = int(sys.argv[5])
        TMPSpaceWidthInPixels = int(sys.argv[6])
#        TMPdeductKerningPixels = int(sys.argv[7])
        TMPcustomBaseLineOffset = 0
        myGrabInstance = grabberFromPNG('windows-1253') #, grabberFromPNG.BR_GameID)
        myGrabInstance.setImageRowFilePNG(TMPimageRowFilePNG)
        myGrabInstance.setTargetFONFilename(TMPTargetFONfilename)
        myGrabInstance.setMinSpaceBetweenLettersInRowLeftToLeft(TMPminSpaceBetweenLettersInRowLeftToLeft)
        myGrabInstance.setMinSpaceBetweenLettersInColumnTopToTop(TMPminSpaceBetweenLettersInColumnTopToTop)
        myGrabInstance.setKerningForFirstDummyFontLetter(TMPkerningForFirstDummyFontLetter)
        myGrabInstance.setSpaceWidthInPixels(TMPSpaceWidthInPixels)
#        myGrabInstance.setDeductKerningPixels(TMPdeductKerningPixels)
#        myGrabInstance.setReconstructEntireFont(TMPreconstructEntireFont)

        myGrabInstance.generateModFiles(TMPcustomBaseLineOffset)
    else:
        print "Invalid syntax! ..."
#        myGrabInstance = grabberFromPNG('windows-extra') #, grabberFromPNG.BR_GameID)
else:
    #debug
	#print 'font grabber imported from another module'
    pass
