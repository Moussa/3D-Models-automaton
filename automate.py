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
	
def automateDis(model, numberOfImages=24, rotationOffset=None):
	""" Method to automize process of taking images for 3D model views. 
	
		Parameters:
                model -> An instance of a HLMVModelRegistryKey object for the model. Required.
				numberOfImages -> Number of images to take for one full rotation. Optional, will default to 24.
				rotationOffset -> The distance from the default centre of rotation to the new one (in HLMV units). Optional.
	"""
	n = 0
	startingpoint = [model.returnTranslation()['x'], model.returnTranslation()['y'], model.returnTranslation()['z']]
	initialrotation = [model.returnRotation()['x'], model.returnRotation()['y'], model.returnRotation()['z']]
	mouse.sleep(3)
	
	for yrotation in range(-180, 180, 360/numberOfImages):
		print 'n =', str(n)
		for xrotation in range(-15, 30, 15):
			# Close HLMV
			mouse.click(x=monitorResolution[0],y=0)
			# Set rotation
			mouse.sleep(2)
			if initialrotation[1] < 0.0:
				initialrotation[1] = 360.0 - abs(initialrotation[1])
			model.setRotation(x = float(initialrotation[0]), y = float(initialrotation[1]) - float(yrotation), z = float(xrotation))
			print 'rotation =', xrotation, yrotation
			if rotationOffset is not None:
				# Set translation to account for off centre rotation
				result = rotateAboutNewCentre(startingpoint[0], startingpoint[1], startingpoint[2], rotationOffset, yrotation, xrotation)
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
			# Change BG colour to black
			mouse.find({targetImagesDir + os.sep + 'optionsmenubutton.png': (0, 0)}, clickpoint=True)
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
			if xrotation == -15:
				imgname = str(n) + 'up.png'
			elif xrotation == 15:
				imgname = str(n) + 'down.png'
			else:
				imgname = str(n) + '.png'
			img.save(outputImagesDir + os.sep + imgname, "PNG")
		n += 1
	# Close HLMV finally
	mouse.click(x = monitorResolution[0], y = 0)
	# Stitch images together
	print 'Stitching images together...'
	stitch(outputImagesDir, finalImageName)
	# All done yay
	print '\nAll done'

# Example Usage for Flare Gun
model = HLMVModelRegistryKey('models.weapons.c_models.c_pocket_watch.parts.c_pocket_watch.mdl')
automateDis(model=model)