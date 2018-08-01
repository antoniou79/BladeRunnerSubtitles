# BladeRunnerSubtitles

# Blade Runner (1997) Subtitles Support
Some tools written in Python 2.7 to help add support for subtitles in Westwood's point and click adventure game Blade Runner (1997) for PC.

## QuotesSpreadsheetCreator (TBD)
A tool to gather all the speech audio filenames in an Excel file including a column with links to the audio file location on the PC.
Prerequisite: extraction of the audio files in WAV format using a modified version of the br-mixer tool. This Excel file should help transcribe all the spoken (in-game) quotes. It also provides extra quote information such as the corresponding actor ID and quote ID.
Note: This tool is depended on the output of another 3rd party program (br-mixer, which is also a bit modified). Additionally, a lot of extra information has been added to the output Excel file, such as whether a quote is unused or untriggered, who the quote refers to (when applicable), as well as extra quotes that are not separate Audio files (AUD) in the game's archives but are part of a video file (VQA). Therefore, this tool is provided here mostly for archiving purposes.

## mixResourceCreator (TBD)
A tool to process the aforementioned Excel file with the dialogue transcriptions and output text resource files (TRE) that will be packed along with the external font (see fontCreator tool) into a SUBTITLES.MIX file. Currently, a modified version of the ScummVM's BladeRunner engine is required for this MIX file to work in-game. Multiple TRE files will be created intermediately in order to fully support subtitles in the game. One TRE file includes all in-game spoken quotes and the rest of them correspond to any VQA video sequence that contain voice acting.

## fontCreator (grabberFromPNG##BR)
A tool to support the creation of a font file (FON) for use with (currently) a modified version of ScummVM's BladeRunner engine (WIP) in order to resolve various issues with the available fonts (included in the game's own resource files). These issues include alignment, kerning, corrupted format, limited charset and unsupported characters -- especially for languages with too many non-latin symbols in their alphabet.
This font tool's code is based off the Monkey Island Special Edition's Translator (https://github.com/ShadowNate/MISETranslator).
Usage:
```
python2.7 grabberFromPNG17BR.py <imageRowPNGFilename> <targetFONfilename> <minSpaceBetweenLettersInRowLeftToLeft> <minSpaceBetweenLettersInColumnTopToTop> <kerningForFirstDummyFontGlyph> <whiteSpaceWidthPx>
```
The tool also __requires__ an overrideEncoding.txt file to be in the same folder as the tool's source (.py) file.
The overrideEncoding.txt is a text file that contains the following:
1. The name of the ascii codepage that should be used for the character fonts (eg windows-1253).
2. A string with all the printable characters that will be used in-game, from the specified codepage. Keep in mind that:
    * The first such character (typically this is the '!' character) should be repeated twice!
    * All characters must belong to the specified codepage.
    * The order that the characters appear in the string should match their order in the ascii table of the codepage.
    * You don't need to use all the characters in the specified codepage.
    * For any special characters that don't appear in the target codepage (eg ñ, é, í, â don't appear in the Greek codepage), you'll have to decide on an ascii value for them (one not used by another character that will appear in-game). 
    In the all-characters string you should use as placeholders the actual characters from the specified codepage that correspond to these ascii values you have selected, and in the proper order.
    * The text file should be saved in a UTF-8 encoding (no BOM)
    * There is a sample of such file in the source folder for the fontCreator tool
3. A list of comma separated tuples that specifies a characters and its manually set kerning (x-offset) in pixels. Kerning can have integer (positive or negative) values. This list is optional and can be skipped if you put a '-' instead of a list.
    * Example: i:-1
    * Don't use space(s) between the tuples!
4. A list of comma separated tuples that specifies a characters and its manually set extended width in pixels. This should be a positive integer value. You can skip this list by not writing anything in the file after the previous (manual kerning) list.
    * Example: i:0,j:1,l:1
    * Don't use space(s) between the tuples!

There are six (6) mandatory launch arguments for the fontCreator tool:
1. imageRowPNGFilename: is the filename of the input PNG image file which should contain a row of (preferably) tab separated glyphs. Example: "Tahoma_18ShdwTranspThreshZero003-G5.png". Keep in mind that:
    * The first glyph should be repeated here too, as in the overrideEncoding.txt file.
	* Background should be transparent.
	* [TBC] all colors used in the character glyphs should not have any transparency value (eg from Gimp 2, set Layer->Transparency->Threshold alpha to 0).
    * If you use special glyphs that are not in the specified ascii codepage (eg ñ, é, í, â don't appear in the Greek codepage), then in this image file you should use the actual special glyphs at the position of the placeholder characters you've had in the overrideEncoding.txt file
2. targetFONfilename: Example: "SUBTITLES.FON". Keep in mind that:
    * As of yet only the SUBTITLES.FON is supported by a modified (non-official) version of the BladeRunner ScummVM engine.
3. minSpaceBetweenLettersInRowLeftToLeft: This is a length (positive integer) in pixels that indicates the __minimum__ distance between the left-most side of a glyph and the left-most side of the immediate subsequent glyph in the input image PNG (row of glyphs) file.
This basically tells the tool how far (in the x axis) it can search for pixels that belong to the same glyph). You can input an approximate value here and adjust it based on the output of the tool (the tool should be able to detect ALL the glyphs in the PNG row image file and it will report how many it detected in its output)
4. minSpaceBetweenLettersInColumnTopToTop: This is a positive integer in pixels that indicates the __minimum__ distance between the top-most pixel of a glyph and the top-most pixel of a glyph on another row of the input image file.
It is highly recommended though that the input image file should contain only a single row of glyphs and this value should be higher than the maximum height among the glyphs, typically this should be set to approximately double the maximum height of glyph.
5. kerningForFirstDummyFontGlyph: This is an integer that explicitly indicates the kerning, ie offset in pixels (on the x-axis) of the first glyph (the one that is repeated twice). This can be measured by observing the indent that your image processing app adds when you enter the first glyph (typically it should be only a few pixels)
6. whiteSpaceWidthPx: This is a positive integer value that sets the width in pixels for the single white space between words for the subtitles in-game.

# Credits and Special Thanks
- All the developer guys from the ScummVM (https://github.com/scummvm/scummvm) team, and especially the ones involved in the implementation of the BladeRunner engine for ScummVM (madmoose, peterkohaut, sev and everyone else).
- The information provided in this blog (http://westwoodbladerunner.blogspot.ca) by Michael Liebscher.
- The creator of br-mixer (https://github.com/bdamer/br-mixer), Ben Damer, who also has a blog entry about the game resource file formats (http://afqa123.com/2015/03/07/deciphering-blade-runner/)
- Any beta testers :)
