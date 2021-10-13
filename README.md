# Hero Designer .hdc to MapTools .rptok converter

The Python script converts a Hero Designer .hdc file into a MapTools .rptok file usable in Scubba's 5th Edition Hero System framework (https://github.com/Scubba/maptool_hero5e).

This only works for Hero 5th Edition characters, 6th Edition is not supported at this time.

## Installation:
Download all of the files to a local folder.  The converter makes use of the `sample.rptok` as the template file, updating and replacing properties and creating a new token file.

Run the `make.sh` (Mac/Linux) to create a zipped distribution of the files.

## Operation:

(Windows) Drag your HeroDesigner .hdc file on the hdc_to_token.bat file in the File Explorer.  You should see a .rptok file created in the same folder as your .hdc file.  The results of the conversion will be output to output.txt.

(Mac/Linux) Use a shell command-line to execute the following:
  `python3 hdc_to_token.py filename1.hdc (filename2.hdc ...)`

# Notes v0.1:
- There are several powers, skills, talents, perks, disadvantages, and modifiers that are not completed at this time.  In this case, review the output of the conversion and review any error messages that are emitted.
