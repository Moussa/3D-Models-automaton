import mouse, Image, ImageGrab, os, subprocess, math
from HLMVModel import *
from SendKeys import SendKeys
try:
	import psyco
	psyco.full()
except:
	pass

degreesToRadiansFactor = math.pi / 180.0
outputImagesDir = r'output\\' # The directory where the output images will be saved.
targetImagesDir = r'targetimages\\' # The directory containing the target images for mouse clicking.
monitorResolution = [1920, 1080] # The monitor resolution of the user in the form of a list; [pixel width, pixel height].
imgCropBoundaries = (280, 42, 1640, 799) # The cropping boundaries, as a pixel distance from the top left corner, for the images as a tuple; (left boundary, top boundary, right boundary, bottom boundary).

def rotateAboutNewCentre(currentXPosition, currentYPosition, lengthOfModel, angle):
	""" Method to position a model in HLMV with a new center of rotation.
	
		Parameters:
                currentXPosition -> The current x position of the model.
				currentYPosition -> The current y position of the model.
				lengthOfModel -> The length of the model (in HLMV units).
				angle -> The angle the model has been rotated by around the y axis.
	"""
	angle = float(angle)
	if angle < 0.0:
		angle = 360.0 - abs(angle) # Funky HLMV coordinate system
	newX = (lengthOfModel * math.cos(angle * degreesToRadiansFactor) / 2.0) + float(currentXPosition)
	newY = (lengthOfModel * math.sin(angle * degreesToRadiansFactor) / 2.0) + float(currentYPosition)
	return [newX, newY]

"""
def toAlpha(weights):
	def getBrightness(p):
		return int((299.0 * p[0] + 587.0 * p[1] + 114.0 * p[2]) / 1000.0)
	imgs = {}
	loaded = {}
	totalImages = len(weights)
	totalWeight = 0
	size = None
	blackImg = None
	loadedBlack = None
	for i in weights:
		imageobject, imageweight = i
		imgs[i] = imageobject.convert('RGBA')
		if size is None:
			size = imgs[i].size
		if imageweight:
			loaded[i] = imgs[i].load()
			totalWeight += imageweight
		else:
			blackImg = i
			loadedBlack = imgs[i].load()
	if blackImg is None:
		return None
	finalImg = Image.new('RGBA', size)
	finalLoad = finalImg.load()
	for x in range(size[0]):
		for y in range(size[1]):
			blackPixel = loadedBlack[x, y]
			totalRed = blackPixel[0]
			totalGreen = blackPixel[1]
			totalBlue = blackPixel[2]
			totalBrightnessDelta = 0
			initialBrightness = getBrightness(blackPixel)
			for i in loaded:
				p = loaded[i][x, y]
				totalRed += p[0]
				totalGreen += p[1]
				totalBlue += p[2]
				brightness = getBrightness(p)
				totalBrightnessDelta += brightness - initialBrightness
			finalLoad[x, y] = (
				int(totalRed / totalImages),
				int(totalGreen / totalImages),
				int(totalBlue / totalImages),
				int(255 - 255 * totalBrightnessDelta / totalWeight)
			)
	return finalImg
"""

def removeBackground(blackBG, whiteBG):
	""" Method to add transparent background for an image.
	
		Parameters:
                blackBG -> The image with a black background.
				whiteBG -> The image with a white background.
	"""
	blackBG = blackBG.convert("RGBA")
	whiteBG = whiteBG.convert("RGBA")
	blackpixdata = blackBG.load()
	whitepixdata = whiteBG.load()

	for y in xrange(blackBG.size[1]):
		for x in xrange(blackBG.size[0]):
			if blackpixdata[x, y] == (0, 0, 0, 255) and whitepixdata[x, y] == (255, 255, 255, 255):
				blackpixdata[x, y] = (0, 0, 0, 0)
			elif blackpixdata[x, y] != whitepixdata[x, y]:
				newred = int(float(blackpixdata[x, y][0] + whitepixdata[x, y][0]) / 2.0)
				newgreen = int(float(blackpixdata[x, y][1] + whitepixdata[x, y][1]) / 2.0)
				newblue = int(float(blackpixdata[x, y][2] + whitepixdata[x, y][2]) / 2.0)
				newalpha = int(float(abs(blackpixdata[x, y][0] - whitepixdata[x, y][0]) + abs(blackpixdata[x, y][1] - whitepixdata[x, y][1]) + abs(blackpixdata[x, y][2] - whitepixdata[x, y][2])) / 3.0)
				blackpixdata[x, y] = (newred, newgreen, newblue, newalpha)
	return blackBG

"""
def stitchImages(fileLocation, numberOfImages):
	imageSize = Image.open(fileLocation + '0.png').size
	finalImageSize = (imageSize[0] * numberOfImages, imageSize[1])
	finalImg = Image.new('RGBA', finalImageSize)
	for imagenumber in range(0, numberOfImages):
		currentimage = Image.open(fileLocation + str(imagenumber) + '.png')
		finalImg.paste(currentimage, (imagenumber * imageSize[0], 0))
	finalImg.save(fileLocation + 'output.png', 'PNG')
"""

def stitchImages2(fileLocation, numberOfImages):
	""" Method to stitch together multiple images after they are taken.
	
		Parameters:
                fileLocation -> The location of the files to be stitched.
				numberOfImages -> Number of images (in one plane) to stitch.
	"""
	imageSize = Image.open(fileLocation + '0.png').size
	finalImageSize = (imageSize[0] * numberOfImages, imageSize[1] * 3)
	finalImg = Image.new('RGBA', finalImageSize)
	for imagenumber in range(0, numberOfImages):
		currentupimage = Image.open(fileLocation + str(imagenumber) + 'up.png')
		currentimage = Image.open(fileLocation + str(imagenumber) + '.png')
		currentdownimage = Image.open(fileLocation + str(imagenumber) + 'down.png')
		finalImg.paste(currentupimage, (imagenumber * imageSize[0], 0))
		finalImg.paste(currentimage, (imagenumber * imageSize[0], imageSize[1]))
		finalImg.paste(currentdownimage, (imagenumber * imageSize[0], imageSize[1] * 2))
	finalImg.save(fileLocation + 'output.png', 'PNG')
	
def automateDis(model, numberOfImages=24, modelLength=None, pngcrush=False):
	""" Method to automize process of taking images for 3D model views. 
	
		Parameters:
                model -> An instance of a HLMVModelRegistryKey object for the model. Required.
				numberOfImages -> Number of images to take for one full rotation. Optional, will default to 24.
				modelLength -> The length of a model. Used in the case of models that do not rotate about the centre of the model. Optional.
				pngcrush -> Boolean to pngcrush final image. Optional, will default to False.
	"""
	n = 0
	startingpoint = [model.returnTranslation()['x'], model.returnTranslation()['y']]
	mouse.sleep(3)
	
	for yrotation in range(-180, 180, 360/numberOfImages):
		print 'n =', str(n)
		for xrotation in range (-20, 40, 20):
			# Close HLMV
			mouse.click(x=monitorResolution[0],y=0)
			# Set rotation
			mouse.sleep(2)
			model.setRotation(x = xrotation, y = yrotation)
			print 'rotation =', xrotation, yrotation
			if modelLength is not None:
				# Set translation
				result = rotateAboutNewCentre(startingpoint[0], startingpoint[1], modelLength, yrotation)
				print 'translation =', result
				model.setTranslation(x = result[0], y = result[1])
			# Set white colour
			model.setBGColour(255, 255, 255, 255)
			# Open HLMV
			mouse.sleep(1)
			x = mouse.find({targetImagesDir + 'openhlmv.png': (0, 0)})
			if x is None:
				x = mouse.find({targetImagesDir + 'openhlmvunhighlighted.png': (0, 0)})
			if x is None:
				x = mouse.find({targetImagesDir + 'openhlmvinactive.png': (0, 0)})
			if x is None:
				print 'Couldn\'t find source SDK launcher to click on'
				break
			mouse.doubleclick(x)
			# Maximise HLMV
			mouse.sleep(2)
			SendKeys("""*{UP}""")
			# Open recent model
			mouse.find({targetImagesDir + 'filemenubutton.png': (0, 0)}, clickpoint=True)
			SendKeys("""{DOWN 8}{RIGHT}{ENTER}""")
			# Take whiteBG screenshot and crop
			mouse.sleep(2)
			imgWhiteBG = ImageGrab.grab()
			imgWhiteBG = imgWhiteBG.crop(imgCropBoundaries)
			# Change BG colour to black
			mouse.find({targetImagesDir + 'optionsmenubutton.png': (0, 0)}, clickpoint=True)
			SendKeys("""{DOWN}{ENTER}""")
			mouse.sleep(1)
			SendKeys("""{LEFT 7}{SPACE}{ENTER}""")
			# Take blackBG screenshot and crop
			mouse.sleep(1)
			imgBlackBG = ImageGrab.grab()
			imgBlackBG = imgBlackBG.crop(imgCropBoundaries)
			# Remove background from image
			img = removeBackground(imgBlackBG, imgWhiteBG)
			# Save screenshot
			if xrotation == -20:
				imgname = str(n) + 'up.png'
			elif xrotation == 20:
				imgname = str(n) + 'down.png'
			else:
				imgname = str(n) + '.png'
			img.save(outputImagesDir + imgname, "PNG")
		n += 1
	# Close HLMV finally
	mouse.click(x = monitorResolution[0], y = 0)
	# Stitch images together
	print 'Stitching images together...'
	stitchImages2(outputImagesDir, numberOfImages)
	# Crush images if specified
	if pngcrush:
		files = os.listdir(outputImagesDir)
		files.sort()
		for file in files:
			print "Processing " + file + "..."
			print outputImagesDir
			outpoot = file[:-4] + r'compressed.png'
			subprocess.call(['pngcrush', '-rem', 'gAMA', '-rem', 'cHRM', '-rem', 'iCCP', '-rem', 'sRGB', '-brute', outputImagesDir + file, outputImagesDir + outpoot])
	# All done yay
	print '\nAll done'

# Example Usage for Flare Gun
model = HLMVModelRegistryKey('models.weapons.c_models.c_flaregun_pyro.c_flaregun_pyro.mdl')
automateDis(model=model, numberOfImages=24, modelLength=19.0)