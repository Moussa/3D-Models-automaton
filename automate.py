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
finalImageName = r'outpoot.jpg' # The name of the final image.
SDKLauncherStartingPoint = (20, 20) # Rough x, y screen coordindates of SDK Launcher. This is near the top left of the screen by default.
monitorResolution = [1920, 1080] # The monitor resolution of the user in the form of a list; [pixel width, pixel height].
imgCropBoundaries = (1, 42, 1919, 799) # The cropping boundaries, as a pixel distance from the top left corner, for the images as a tuple; (left boundary, top boundary, right boundary, bottom boundary).
fileButtonCoordindates = (14, 32) # The coordinates for the File menu button in HLMV
optionsButtonCoodinates = (55, 32) # The coordinates for the Options menu button in HLMV

def getBrightness(p):
	return (299.0 * p[0] + 587.0 * p[1] + 114.0 * p[2]) / 1000.0

def toAlphaBlackWhite(blackImg, whiteImg):
	size = blackImg.size
	blackImg = blackImg.convert('RGBA')
	loadedBlack = blackImg.load()
	loadedWhite = whiteImg.load()
	for x in range(size[0]):
		for y in range(size[1]):
			blackPixel = loadedBlack[x, y]
			whitePixel = loadedWhite[x, y]
			loadedBlack[x, y] = (
				(blackPixel[0] + whitePixel[0]) / 2,
				(blackPixel[1] + whitePixel[1]) / 2,
				(blackPixel[2] + whitePixel[2]) / 2,
				int(255.0 - 255.0 * (getBrightness(whitePixel) - getBrightness(blackPixel)))
			)
	return blackImg

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

def offsetVertically(currentXPosition, currentYPosition, currentZPosition, verticalOffset, yangle, xangle):
	yangle = float(yangle)
	verticalOffset = float(verticalOffset)
	if yangle < 0.0:
		yangle = 360.0 - abs(yangle) # Funky HLMV coordinate system
	newX = ((math.sin(xangle * degreesToRadiansFactor)) * (math.sin(yangle * degreesToRadiansFactor)) * verticalOffset) + float(currentXPosition)
	newY = ((math.sin(yangle * degreesToRadiansFactor)) * (math.sin(xangle * degreesToRadiansFactor)) * verticalOffset) + float(currentYPosition)
	newZ = currentZPosition
	return [newX, newY, newZ]
	
def automateDis(model, numberOfImages=24, n=0, rotationOffset=None, initialRotation=None, initialTranslation=None, verticalOffset=None, disableXRotation=False):
	""" Method to automize process of taking images for 3D model views. 
	
		Parameters:
                model -> An instance of a HLMVModelRegistryKey object for the model. Required.
				numberOfImages -> Number of images to take for one full rotation. Optional, default is 24.
				n -> Which nth step of rotation to start at. Optional, default is 0.
				rotationOffset -> The distance from the default centre of rotation to the new one (in HLMV units). Optional, default is none.
				initialRotation -> The initial model rotation as a tuple. Optional, default is (0 0 0).
				initialTranslation -> The initial model translation as a tuple. Optional, default is (0 0 0).
				verticalOffset -> The vertical offset for models that are centered in both other planes but not vertically. Optional, default is none.
				disableXRotation -> Boolean that disables tilting. Default is False.
	"""
	
	folder = raw_input('Folder name for created images: ')
	outputFolder = outputImagesDir + os.sep + folder
	try:
		os.mkdir(outputFolder)
	except:
		answer = raw_input('Folder already exists, overwrite files? y\\n? ')
		if answer == 'yes' or answer == 'y':
			pass
		elif answer == 'no' or answer == 'n':
			sys.exit(1)
	
	if initialTranslation is None:
		initialTranslation = [model.returnTranslation()['x'], model.returnTranslation()['y'], model.returnTranslation()['z']]
	if initialRotation is None:
		initialRotation = [model.returnRotation()['x'], model.returnRotation()['y'], model.returnRotation()['z']]
	mouse.sleep(3)
	
	mouse.click(x=monitorResolution[0],y=0)
	mouse.sleep(2)
	print 'initialTranslation =', initialTranslation
	print 'initialRotation =', initialRotation
	model.setTranslation(x = initialTranslation[0], y = initialTranslation[1], z = initialTranslation[2])
	model.setNormalMapping(True)
	SDKLauncherCoords = None
	
	for yrotation in range((-180 + (360/24 * n)), 180, 360/numberOfImages):
		print 'n =', str(n)
		for xrotation in range(-15, 30, 15):
			if (disableXRotation and xrotation == 0) or not disableXRotation:
				# Set rotation
				mouse.sleep(2)
				model.setRotation(x = xrotation + float(initialRotation[0]), y = yrotation + float(initialRotation[1]), z = initialRotation[2])
				print 'xRot = %s, yRot = %s' % (xrotation, yrotation)
				if rotationOffset is not None:
					# Set translation to account for off centre rotation
					result = rotateAboutNewCentre(initialTranslation[0], initialTranslation[1], initialTranslation[2], rotationOffset, yrotation, xrotation)
					print 'translation =', result
					model.setTranslation(x = result[0], y = result[1], z = result[2])
					# Set translation to account for off centre horizontal rotation
				elif verticalOffset is not None:
					result = offsetVertically(initialTranslation[0], initialTranslation[1], initialTranslation[2], verticalOffset, yrotation, xrotation)
					print 'translation =', result
					model.setTranslation(x = result[0], y = result[1], z = result[2])
				# Set white colour
				model.setBGColour(255, 255, 255, 255)
				# Open HLMV
				mouse.sleep(1)
				if SDKLauncherCoords is None:
					SDKLauncherCoords = mouse.find({targetImagesDir + os.sep + 'openhlmv.png': (0, 0)}, startingPoint=SDKLauncherStartingPoint)
					if SDKLauncherCoords is None:
						SDKLauncherCoords = mouse.find({targetImagesDir + os.sep + 'openhlmvunhighlighted.png': (0, 0)}, startingPoint=SDKLauncherStartingPoint)
					if SDKLauncherCoords is None:
						SDKLauncherCoords = mouse.find({targetImagesDir + os.sep + 'openhlmvinactive.png': (0, 0)}, startingPoint=SDKLauncherStartingPoint)
					if SDKLauncherCoords is None:
						print 'Couldn\'t find source SDK launcher to click on'
						break
				mouse.doubleclick(SDKLauncherCoords)
				# Maximise HLMV
				mouse.sleep(2)
				SendKeys("""*{UP}""")
				# Open recent model
				mouse.click(x=fileButtonCoordindates[0],y=fileButtonCoordindates[1])
				SendKeys("""{DOWN 8}{RIGHT}{ENTER}""")
				# Take whiteBG screenshot and crop
				mouse.sleep(2)
				imgWhiteBG = ImageGrab.grab()
				imgWhiteBG = imgWhiteBG.crop(imgCropBoundaries)
				# Change BG colour to black
				mouse.click(x=optionsButtonCoodinates[0],y=optionsButtonCoodinates[1])
				SendKeys("""{DOWN}{ENTER}""")
				mouse.sleep(1)
				SendKeys("""{LEFT 7}{SPACE}{ENTER}""")
				# Take blackBG screenshot and crop
				mouse.sleep(1)
				imgBlackBG = ImageGrab.grab()
				imgBlackBG = imgBlackBG.crop(imgCropBoundaries)
				# Remove background from image
				img = toAlphaBlackWhite(imgBlackBG, imgWhiteBG)
				# Save screenshot
				if xrotation == -15:
					imgname = str(n) + 'up.png'
				elif xrotation == 15:
					imgname = str(n) + 'down.png'
				else:
					imgname = str(n) + '.png'
				img.save(outputFolder + os.sep + imgname, "PNG")
				# Close HLMV
				mouse.click(x=monitorResolution[0],y=0)
		n += 1
	# Stitch images together
	print 'Stitching images together...'
	stitch(outputFolder, finalImageName)
	# All done yay
	print '\nAll done'

# Poot values here
model = HLMVModelRegistryKey('models.weapons.c_models.c_rift_fire_axe.c_rift_fire_axe.mdl')
automateDis(model=model,
			n=0,
			rotationOffset=None,
			verticalOffset=None,
			disableXRotation=False,
			initialRotation=(0.000000, 0.000000, 0.000000),
			initialTranslation=(107.167007, 0.000000, 2.749039)
			)