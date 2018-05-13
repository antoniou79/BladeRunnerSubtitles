# BladeRunnerSubtitles

Blade Runner (1997) Subtitles Support
============================================
Some tools written in Python 2.7 to help add support for subtitles in Westwood's point and click adventure game Blade Runner (1997) for PC. 

* A tool to gather all the speech audio filenames in an Excel file including a column with links to the audio file location on the PC. Prerequisite: extraction of the audio files in WAV format using a modified version of the br-mixer tool. This Excel file should help transcribe all the spoken (in-game) quotes. It also provides extra quote information such as the corresponding actor ID and quote ID.
Note: This tool is depended on the output of another 3rd party program (br-mixer, which is also a bit modified). Additionally, a lot of extra information has been added to the output Excel file, such as whether a quote is unused or untriggered, who the quote refers to (when applicable), as well as extra quotes that are not separate Audio files (AUD) in the game's archives but are part of a video file (VQA). Therefore, this tool is provided here mostly for archiving purposes.

* A tool to process the aforementioned Excel file with the dialogue transcriptions and output a text resource file (TRE) that can be used by the game's engine. Currently, a modified version of the ScummVM's BladeRunner engine is required for this external TRE file to work in-game. Multiple TRE files should be created in order to fully support subtitles in the game. One TRE file will include all in-game spoken quotes, and the rest of them are one TRE file per VQA video sequence which includes voice acting.  

* A tool to support the creation of a font file (FON) for use with (currently) a version modified ScummVM BladeRunner engine in order to resolve various issues with the available fonts (included in the game's own resource files). These issues include alignment, kerning, limited charset and unsupported characters -- especially for languages with too many non-latin symbols in their alphabet. The current plan is to base this tool's code off the the Monkey Island Special Edition's Translator.

Credits and Special Thanks
============================================
- All the developer guys from the ScummVM (https://github.com/scummvm/scummvm) team, and especially the ones involved in the implementation of the BladeRunner engine for ScummVM (madmoose, peterkohaut, sev and everyone else).
- The information provided in this blog (http://westwoodbladerunner.blogspot.ca) by Michael Liebscher.
- The creator of br-mixer (https://github.com/bdamer/br-mixer), Ben Damer, who also has a blog entry about the game resource file formats (http://afqa123.com/2015/03/07/deciphering-blade-runner/)
- Any beta testers :)
