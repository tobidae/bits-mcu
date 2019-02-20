# BITS-pi

## Installation

## Some workarounds
Due to how text detection is setup in this project,
the tessaract english trained data needs to be replaced with one from this 
[link](https://github.com/tesseract-ocr/tessdata/blob/master/eng.traineddata) or the helpers/eng.traineddata file. The file is located at 
/usr/local/bin/tesseract. Alternatively, using the `which tesseract` command in terminal will give you an accurate
location of where tesseract is located on your machine.