import mouse, Image, ImageGrab, os, subprocess, math
from HLMVModel import *
from SendKeys import SendKeys
from Stitch import *
try:
	import psyco
	psyco.full()
except:
	pass

degreesToRadiansFactor = math.pi / 180.0
outputImagesDir = r'output' # The directory where the output images will be saved.
targetImagesDir = r'targetimages' # The directory containing the target images for mouse clicking.
finalImageName = r'outpoot.jpg'
monitorResolution = [1920, 1080] # The monitor resolution of the user in the form of a list; [pixel width, pixel height].
imgCropBoundaries = (1, 42, 1919, 799) # The cropping boundaries, as a pixel distance from the top left corner, for the images as a tuple; (left boundary, top boundary, right boundary, bottom boundary).

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
		imgs[i] = Image.open(i)
		if size is None:
			size = imgs[i].size
		if weights[i]:
			loaded[i] = imgs[i].load()
			totalWeight += weights[i]
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

def rotateAboutNewCentre(currentXPosition, currentYPosition, currentZPosition, rotationOffset, yangle, xangle):
	""" Method to position a model in HLMV with a new center of rotation.
	
		Parameters:
                currentXPosition -> The current x position of the model.
				currentYPosition -> The current y position of the model.
				currentZPosition -> The current z position of the model.
				rotationOffset -> The distance from the default centre of rotation to the new one (in HLMV units).
				yangle -> The angle the model has been rotated by around the y axis.
				xangle -> The angle the model has been rotated by around the x axis.
	"""
	yangle = float(yangle)
	xangle = float(xangle)
	rotationOffset = float(rotationOffset)
	if yangle < 0.0:
		yangle = 360.0 - abs(yangle) # Funky HLMV coordinate system
	newX = (math.cos(yangle * degreesToRadiansFactor) * rotationOffset) + float(currentXPosition)
	newY = (math.sin(yangle * degreesToRadiansFactor) * rotationOffset) + float(currentYPosition)
	newZ = float(currentZPosition) - (math.sin(xangle * degreesToRadiansFactor) * rotationOffset)
	return [newX, newY, newZ]

def tiltAboutNewCentre(currentXPosition, currentYPosition, currentZPosition, tiltOffset, yangle, xangle):
	yangle = float(yangle)
	xangle = float(xangle)
	tiltOffset = float(tiltOffset)
	if yangle < 0.0:
		yangle = 360.0 - abs(yangle) # Funky HLMV coordinate system
	newX = (math.cos(yangle * degreesToRadiansFactor) * tiltOffset) + float(currentXPosition)
	newY = currentYPosition
	newZ = float(currentZPosition) - (math.sin(xangle * degreesToRadiansFactor) * tiltOffset)
	return [newX, newY, newZ]
	
def automateDis(model, numberOfImages=24, n=0, rotationOffset=None, initialRotation=None, initialTranslation=None, tiltOffset=None):
	""" Method to automize process of taking images for 3D model views. 
	
		Parameters:
                model -> An instance of a HLMVModelRegistryKey object for the model. Required.
				numberOfImages -> Number of images to take for one full rotation. Optional, will default to 24.
				rotationOffset -> The distance from the default centre of rotation to the new one (in HLMV units). Optional.
	"""
	if initialTranslation is None:
		initialTranslation = [model.returnTranslation()['x'], model.returnTranslation()['y'], model.returnTranslation()['z']]
	if initialRotation is None:
		initialRotation = [model.returnRotation()['x'], model.returnRotation()['y'], model.returnRotation()['z']]
	mouse.sleep(3)
	
	print 'initialTranslation =', initialTranslation
	print 'initialRotation =', initialRotation
	
	for yrotation in range((-180 + (360/24 * n)), 180, 360/numberOfImages):
		print 'n =', str(n)
		for xrotation in range(-15, 30, 15):
			# Close HLMV
			mouse.click(x=monitorResolution[0],y=0)
			# Set rotation
			mouse.sleep(2)
			model.setRotation(x = xrotation + float(initialRotation[0]), y = yrotation + float(initialRotation[1]), z = initialRotation[2])
			print 'xRot = %s, yRot = %s' % (xrotation, yrotation)
			if rotationOffset is not None:
				# Set translation to account for off centre rotation
				result = rotateAboutNewCentre(initialTranslation[0], initialTranslation[1], initialTranslation[2], rotationOffset, yrotation, xrotation)
				print 'translation =', result
				model.setTranslation(x = result[0], y = result[1], z = result[2])
			elif tiltOffset is not None:
				result = tiltAboutNewCentre(initialTranslation[0], initialTranslation[1], initialTranslation[2], tiltOffset, yrotation, xrotation)
				print 'translation =', result
				model.setTranslation(x = result[0], y = result[1], z = result[2])
			# Set white colour
			model.setBGColour(255, 255, 255, 255)
			# Open HLMV
			mouse.sleep(1)
			x = mouse.find({targetImagesDir + os.sep + 'openhlmv.png': (0, 0)})
			if x is None:
				x = mouse.find({targetImagesDir + os.sep + 'openhlmvunhighlighted.png': (0, 0)})
			if x is None:
				x = mouse.find({targetImagesDir + os.sep + 'openhlmvinactive.png': (0, 0)})
			if x is None:
				print 'Couldn\'t find source SDK launcher to click on'
				break
			mouse.doubleclick(x)
			# Maximise HLMV
			mouse.sleep(2)
			SendKeys("""*{UP}""")
			# Open recent model
			mouse.find({targetImagesDir + os.sep + 'filemenubutton.png': (0, 0)}, clickpoint=True)
			SendKeys("""{DOWN 8}{RIGHT}{ENTER}""")
			# Take whiteBG screenshot and crop
			mouse.sleep(2)
			imgWhiteBG = ImageGrab.grab()
			imgWhiteBG = imgWhiteBG.crop(imgCropBoundaries)
			if xrotation == -15:
				whiteimgname = str(n) + 'whiteup.png'
			elif xrotation == 15:
				whiteimgname = str(n) + 'whitedown.png'
			else:
				whiteimgname = str(n) + 'white.png'
			imgWhiteBG.save(outputImagesDir + os.sep + whiteimgname, "PNG")
			# Change BG colour to black
			mouse.find({targetImagesDir + os.sep + 'optionsmenubutton.png': (0, 0)}, clickpoint=True)
			SendKeys("""{DOWN}{ENTER}""")
			mouse.sleep(1)
			SendKeys("""{LEFT 7}{SPACE}{ENTER}""")
			# Take blackBG screenshot and crop
			mouse.sleep(1)
			imgBlackBG = ImageGrab.grab()
			imgBlackBG = imgBlackBG.crop(imgCropBoundaries)
			if xrotation == -15:
				blackimgname = str(n) + 'blackup.png'
			elif xrotation == 15:
				blackimgname = str(n) + 'blackdown.png'
			else:
				blackimgname = str(n) + 'black.png'
			imgBlackBG.save(outputImagesDir + os.sep + blackimgname, "PNG")
			# Remove background from image
			img = toAlpha({(outputImagesDir + os.sep + whiteimgname): 255,(outputImagesDir + os.sep + blackimgname): 0})
			# Save screenshot
			if xrotation == -15:
				imgname = str(n) + 'up.png'
			elif xrotation == 15:
				imgname = str(n) + 'down.png'
			else:
				imgname = str(n) + '.png'
			img.save(outputImagesDir + os.sep + imgname, "PNG")
			# Remove temp black and white images
			os.remove(outputImagesDir + os.sep + whiteimgname)
			os.remove(outputImagesDir + os.sep + blackimgname)
		n += 1
	# Close HLMV finally
	mouse.click(x = monitorResolution[0], y = 0)
	# Stitch images together
	print 'Stitching images together...'
	stitch(outputImagesDir, finalImageName)
	# All done yay
	print '\nAll done'

# Poot values here
model = HLMVModelRegistryKey('models.weapons.c_models.c_candy_cane.c_candy_cane.mdl')
automateDis(model=model, n=0, rotationOffset=None, initialRotation=(0.000000, -4.000000, 0.000000), initialTranslation=(141.161835, 0.000000, 10.459801), tiltOffset=10.0)