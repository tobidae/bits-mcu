# BITS-pi

## Installation
Tessaract can be installed by using apt-get like so `sudo apt-get install tesseract-ocr -y`
## Some workarounds
Due to how text detection is setup in this project,
the tessaract english trained data needs to be replaced with one from this 
[link](https://github.com/tesseract-ocr/tessdata/blob/master/eng.traineddata) or the helpers/eng.traineddata file. The 
file is located at /usr/share/tesseract-ocr/tessdata/. Alternatively, using the 
`find / -type f -iname "eng.traineddata"` command in terminal will give you an accurate
location of where the tesseract data is located on your machine. Simply copy the traineddata from the site or locally 
to the tessdata location.