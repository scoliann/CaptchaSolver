from PIL import Image
import ImageEnhance
from pytesser import *
import sys
import collections as cl
import os
from os import listdir
from os.path import isfile, join
import re
import Queue
import threading
import numpy


def assignTempName(imgName):

	# Open image and add 'temp' to the name
	originalImage = Image.open(imgName)
	tempName = 'temp_' + imgName.split('\\')[-1]
	originalImage.save(tempName)

	# Return the new temp name
	return tempName


def enlargeImage(imgName):
	# Open original image and resize
	im1 = Image.open(imgName)
	nx, ny = im1.size
	im2 = im1.resize((int(nx*5), int(ny*5)), Image.BICUBIC)

	# Assign new name
	newName = imgName.split('.')[0] + '_enlarged.' + imgName.split('.')[1]
	im2.save(newName)

	# Return newName
	return newName
	

def enhanceImage(imgName, contrastVal):
	# Open image
	im1 = Image.open(imgName)

	# Enhance the resized image
	enhancer = ImageEnhance.Contrast(im1)
	enhanced = enhancer.enhance(contrastVal)

	# Assign new name and save
	newName = imgName.split('.')[0] + '_enhanced' + str(contrastVal) + '.' + imgName.split('.')[1]
	enhanced.save(newName)

	# Return newName
	return newName


def getString(imgName):
	
	# Get the current directory
	currentDir = os.path.dirname(os.path.abspath(__file__)) + '\\'

	# Try to get the string from the image
	im1 = Image.open(imgName)
	text = image_to_string(im1, currentDir)

	# Remove the last two characters from the string, which will be new line characters	
	text = text[:-2]	

	# Return text
	return text


def checkText(text):

	# If the length of the text is less than 3 characters (this includes empty string cases)
	if len(text) < 3:
		return False

	# If the text contains more than one non-numerical-non-alphabetic character
	lowerAlpha = 'abcdefghijklmnopqrstuvwxyz'
	upperAlpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	numbers = '0123456789'
	nonAlphaNum_Counter = 0
	for char in text:
		if not ((char in lowerAlpha) or (char in upperAlpha) or (char in numbers)):
			nonAlphaNum_Counter += 1
	
	if nonAlphaNum_Counter > 1:
		return False

	# Otherwise, return True
	return True


def whiteWashImage(imgName, threshold, thresholdNumber):

	# Open image and convert to a numpy array
	img = Image.open(imgName)
	img = img.convert("RGBA")
	data = numpy.array(img)	

	# Get RGBA values
	red, green, blue, alpha = data.T 					

	# Replace white with red... (leaves alpha values alone...)
	white_areas = (red > threshold) | (blue > threshold) | (green > threshold)	
	black_areas = (red <= threshold) & (blue <= threshold) & (green <= threshold)

	# Make white areas white and black areas black
	data[..., :-1][white_areas.T] = (255, 255, 255) 			
	data[..., :-1][black_areas.T] = (0, 0, 0)

	# Convert the array back to an image and save it
	new_image = Image.fromarray(data)
	newName = imgName.split('.')[0] + '_whitewash' + str(thresholdNumber) + '.' + imgName.split('.')[1]
	new_image.save(newName)

	# Return the next name
	return newName


def processThresholdVal(threshold, whiteWashedImg_name, thresholdVal_queue):

	# Initialize temp_guessCounter
	temp_guessCounter = cl.Counter()

	# Try and draw a rectangle around the center
	imgToCrop = Image.open(whiteWashedImg_name)

	# Cascade over image radiating out from the center
	xLen = imgToCrop.size[0]
	yLen = imgToCrop.size[1]

	centerX = xLen / 2
	centerY = yLen / 2

	xIncrement = xLen / 20
	yIncrement = yLen / 20

	crop_xLen = xLen / 20
	crop_yLen = yLen / 20

	counter = 0
	while (crop_xLen < xLen) and (crop_yLen < yLen):

		# Calculate coordinates for the cropping
		xCoor_1 = centerX - (crop_xLen / 2)	
		yCoor_1 = centerY - (crop_yLen / 2)
		xCoor_2 = centerX + (crop_xLen / 2)	
		yCoor_2 = centerY + (crop_yLen / 2)	

		counter += 1
		testImg = imgToCrop.crop((xCoor_1, yCoor_1, xCoor_2, yCoor_2))
		fileName = whiteWashedImg_name.split('.')[0] + "_cascade" + str(counter) + ".jpg"
		testImg.save(fileName)
		crop_xLen += xIncrement
		crop_yLen += yIncrement
	

		# Get text interpretation and log the results
		text = getString(fileName)

		if checkText(text):
			print "\tPoss Interpretation:\t" + text + "\t" + str(len(text))
			temp_guessCounter[text] += 1

			# Remove non-numerical characters, and add
			text = re.sub("[^0-9]", "", text)
			if len(text) >= 3:
				temp_guessCounter[text] += 1


	# Get text interpretation and log the results
	text = getString(whiteWashedImg_name)

	if checkText(text):
		print "\tPoss Interpretation:\t" + text+ "\t" + str(len(text))
		temp_guessCounter[text] += 1
		
		# Remove non-numerical characters, and add
		text = re.sub("[^0-9]", "", text)
		if len(text) >= 3:
			temp_guessCounter[text] += 1

	# Add temp_guessCounter to queue
	thresholdVal_queue.put(temp_guessCounter)


def processContrastVal(contrastValNumber, enhancedImg_name, thresholdIterations, contrastVal_queue):

	# Run on each threshold value
	temp_guessCounter = cl.Counter()
	threads = []
	thresholdVal_queue = Queue.Queue()
	for i_threshold in range(thresholdIterations):

		# Generate proper thershold value
		thresholdNumber = i_threshold + 1
		threshold = thresholdNumber * 10

		# Generate Whitewashed Image
		whiteWashedImg_name = whiteWashImage(enhancedImg_name, threshold, thresholdNumber)

		# Create threads
		thread = threading.Thread(target=processThresholdVal, args=(threshold, whiteWashedImg_name, thresholdVal_queue))
		thread.start()
		threads.append(thread)

	# Close threads
	for thread in threads:
		thread.join()

	# Empty the queue
	while not thresholdVal_queue.empty():

		# Get result
		temp_temp_guessCounter = thresholdVal_queue.get()

		# Add it to temp_guessCounter
		temp_guessCounter = temp_guessCounter + temp_temp_guessCounter

	# Add output result to a queue
	contrastVal_queue.put(temp_guessCounter)
	

def interpretAllImages(contrastIterations, thresholdIterations, enlargedImg_name):

	# Try variations of images with different contrast values
	guessCounter = cl.Counter()
	threads = []
	contrastVal_queue = Queue.Queue()
	for contrastVal in range(contrastIterations):

		# Increment contrastVal
		contrastValNumber = contrastVal + 1

		enlargedImg = Image.open(enlargedImg_name)
		openName = enlargedImg_name.split('.')[0] + '_contrast' + str(contrastValNumber) + '.' + enlargedImg_name.split('.')[1]
		enlargedImg.save(openName)

		# Enhance the image
		enhancedImg_name = enhanceImage(enlargedImg_name, contrastValNumber)

		# Create threads
		thread = threading.Thread(target=processContrastVal, args=(contrastValNumber, enhancedImg_name, thresholdIterations, contrastVal_queue))
		thread.start()
		threads.append(thread)

	# Close threads
	for thread in threads:
		thread.join()

	# Empty the queue
	while not contrastVal_queue.empty():

		# Get result
		temp_guessCounter = contrastVal_queue.get()

		# Add it to guessCounter
		guessCounter = guessCounter + temp_guessCounter
		
	# Return guessCounter
	return guessCounter


def chooseBestGuess(guessCounter):

	# Only keep the entries that are valid numbers
	print "\nContending Guesses:"
	numbersOnly = cl.defaultdict(str)
	for num in guessCounter:
		recordFlag = True
		for char in num:
			if char not in '0123456789':
				recordFlag = False
		if recordFlag:
			numbersOnly[num] = guessCounter[num]
			print '\t' + num + '\t' + str(guessCounter[num])

	# If numbersOnly is not empty
	if len(numbersOnly) >= 2:

		# Get the largest number from numbersOnly
		allValues = list([numbersOnly[key] for key in numbersOnly])
		maxValue = max(allValues)
		allValues.remove(maxValue)
		secondMaxValue = max(allValues)

		# Check that there is only one entry with maxValue
		counter = 0
		for num in numbersOnly:
			if numbersOnly[num] == maxValue:
				counter += 1
		if counter == 1:

			# Check that the predicted value is at least 3 times larger than the value with the second highest count
			if maxValue > (3 * secondMaxValue):

				# Get the key associated with maxValue
				maxKey = [key for key in numbersOnly if numbersOnly[key] == maxValue][0]				
				return maxKey
	
	# Otherwise, return false
	return "Unable to Guess"


def rmTempImages():
	for ifile in listdir('.'):
		if isfile(join('.', ifile)):
			if ('temp' in ifile):
				os.remove(ifile)


def rmDelete_This():
	for ifile in listdir('.'):
		if isfile(join('.', ifile)):
			if 'delete_this' in ifile:
				os.remove(ifile)


def run(imgPath):

	# Open image and add 'temp' to the name
	tempName = assignTempName(imgPath)

	# Enlarge the image
	enlargedImg_name = enlargeImage(tempName)

	# Try interpreting image under many enhancement, whitewashing, and cascading conditions
	contrastIterations = 4
	thresholdIterations = 15
	guessCounter = interpretAllImages(contrastIterations, thresholdIterations, enlargedImg_name)

	# Choose best guess
	bestGuess = chooseBestGuess(guessCounter)
	
	# Remove all image iterations
	rmTempImages()

	# Remove all 'delete_this' images generated by pytesser.py
	rmDelete_This()

	# Return the best guess
	return bestGuess




if __name__ == "__main__":

	# Original image name
	imgName = 'image.jpg'

	# Run the guessing algorithm
	bestGuess = run(imgName)

	print "\nPrediction: ",str(bestGuess)










