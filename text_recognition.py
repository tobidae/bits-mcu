from imutils.object_detection import non_max_suppression
import imutils
import numpy as np
import pytesseract
import cv2
import sys
from configparser import ConfigParser


class TextRecognition:
    def __init__(self):
        print("[INFO] Starting OCR")
        self.pyconfig = ConfigParser()
        self.pyconfig.read('config.ini')

        print("[INFO] Loading EAST text detector...")
        self.east_detector = self.pyconfig.get('text_recognition', 'east_detector')
        # load the pre-trained EAST text detector
        self.net = cv2.dnn.readNet(self.east_detector)

        self.config_width = self.pyconfig.getint('text_recognition', 'width')
        self.config_height = self.pyconfig.getint('text_recognition', 'height')

        self.min_confidence = self.pyconfig.getfloat('text_recognition', 'min_confidence')
        
    def decode_predictions(self, scores, geometry):
        # grab the number of rows and columns from the scores volume, then
        # initialize our set of bounding box rectangles and corresponding
        # confidence scores
        (numRows, numCols) = scores.shape[2:4]
        rects = []
        confidences = []
    
        # loop over the number of rows
        for y in range(0, numRows):
            # extract the scores (probabilities), followed by the
            # geometrical data used to derive potential bounding box
            # coordinates that surround text
            scoresData = scores[0, 0, y]
            xData0 = geometry[0, 0, y]
            xData1 = geometry[0, 1, y]
            xData2 = geometry[0, 2, y]
            xData3 = geometry[0, 3, y]
            anglesData = geometry[0, 4, y]
    
            # loop over the number of columns
            for x in range(0, numCols):
                # if our score does not have sufficient probability, ignore it
                if scoresData[x] < self.min_confidence:
                    continue
    
                # compute the offset factor as our resulting feature
                # maps will be 4x smaller than the input image
                (offsetX, offsetY) = (x * 4.0, y * 4.0)
    
                # extract the rotation angle for the prediction and
                # then compute the sin and cosine
                angle = anglesData[x]
                cos = np.cos(angle)
                sin = np.sin(angle)
    
                # use the geometry volume to derive the width and height
                # of the bounding box
                h = xData0[x] + xData2[x]
                w = xData1[x] + xData3[x]
    
                # compute both the starting and ending (x, y)-coordinates
                # for the text prediction bounding box
                endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
                endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
                startX = int(endX - w)
                startY = int(endY - h)
    
                # add the bounding box coordinates and probability score
                # to our respective lists
                rects.append((startX, startY, endX, endY))
                confidences.append(scoresData[x])
    
        # return a tuple of the bounding boxes and associated confidences
        return rects, confidences

    def recognize(self, image):
        # grab the image dimensions
        image = imutils.resize(image, width=320)
        orig = image.copy()
        (origH, origW) = image.shape[:2]

        # set the new width and height and then determine the ratio in change
        # for both the width and height
        (newW, newH) = (self.config_width, self.config_height)
        rW = origW / float(newW)
        rH = origH / float(newH)

        # resize the image and grab the new image dimensions
        image = cv2.resize(image, (newW, newH))
        (H, W) = image.shape[:2]

        # define the two output layer names for the EAST detector model that
        # we are interested -- the first is the output probabilities and the
        # second can be used to derive the bounding box coordinates of text
        layer_names = ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]

        # construct a blob from the image and then perform a forward pass of
        # the model to obtain the two output layer sets
        blob = cv2.dnn.blobFromImage(image, 1.0, (W, H), (123.68, 116.78, 103.94), swapRB=True, crop=False)
        self.net.setInput(blob)
        (scores, geometry) = self.net.forward(layer_names)

        # decode the predictions, then  apply non-maxima suppression to
        # suppress weak, overlapping bounding boxes
        (rects, confidences) = self.decode_predictions(scores, geometry)
        boxes = non_max_suppression(np.array(rects), probs=confidences)

        # initialize the list of results
        results = []

        # loop over the bounding boxes
        for (startX, startY, endX, endY) in boxes:
            # scale the bounding box coordinates based on the respective
            # ratios
            startX = int(startX * rW)
            startY = int(startY * rH)
            endX = int(endX * rW)
            endY = int(endY * rH)

            # in order to obtain a better OCR of the text we can potentially
            # apply a bit of padding surrounding the bounding box -- here we
            # are computing the deltas in both the x and y directions
            padding = self.pyconfig.getfloat('text_recognition', 'padding')
            dX = int((endX - startX) * padding)
            dY = int((endY - startY) * padding)

            # apply padding to each side of the bounding box, respectively
            startX = max(0, startX - dX)
            startY = max(0, startY - dY)
            endX = min(origW, endX + (dX * 2))
            endY = min(origH, endY + (dY * 2))

            # extract the actual padded ROI
            roi = orig[startY:endY, startX:endX]

            # in order to apply Tesseract v4 to OCR text we must supply
            # (1) a language, (2) an OEM flag of 4, indicating that the we
            # wish to use the LSTM neural net model for OCR, and finally
            # (3) an OEM value, in this case, 7 which implies that we are
            # treating the ROI as a single line of text
            config = "-l eng --oem 0 -c tessedit_char_whitelist=123ABCDEIGNR --psm 8"
            text = pytesseract.image_to_string(roi, config=config)

            # add the bounding box coordinates and OCR'd text to the list
            # of results
            results.append(((startX, startY, endX, endY), text))

        # sort the results bounding box coordinates from top to bottom
        results = sorted(results, key=lambda r: r[0][1])

        output_data = []
        # loop over the results
        for ((startX, startY, endX, endY), text) in results:
            # strip out non-ASCII text so we can draw the text on the image
            # using OpenCV, then draw the text and a bounding box surrounding
            # the text region of the input image
            text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
            output_data.append(text)

        return output_data


# Test code to check text recognition functionality
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    from jetsonvideostream import JetsonVideoStream
    import time

    print("[INFO] Starting video stream...")
    vs = JetsonVideoStream().start()
    text_rec = TextRecognition()
    time.sleep(2)

    while True:
        test_frame = vs.read()
        test_frame = imutils.resize(test_frame, width=400)

        text_output = text_rec.recognize(test_frame)
        print(text_output)

        time.sleep(1)
