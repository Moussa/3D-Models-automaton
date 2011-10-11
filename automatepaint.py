import mouse, Image, ImageGrab, os, subprocess, math, imgpie, threading, time
from subprocess import Popen, PIPE
from HLMVModel import *
from SendKeys import SendKeys
from StitchPaint import *
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

paintDict = {'Stock': 'Stock',
			 'An Extraordinary Abundance of Tinge': '230 230 230',
			 'Color No. 216-190-216': '216 190 216',
			 'Peculiarly Drab Tincture': '197 175 145',
			 'Aged Moustache Grey': '126 126 126',
			 'A Distinctive Lack of Hue': '20 20 20',
			 'Radigan Conagher Brown': '105 77 58',
			 'Ye Olde Rustic Color': '124 108 87',
			 'Muskelmannbraun': '165 117 69',
			 'Australium Gold': '231 181 59',
			 'The Color of a Gentlemann\'s Business Pants': '240 230 140',
			 'Dark Salmon Injustice': '233 150 122',
			 'Mann Co. Orange': '207 115 54',
			 'Pink as Hell': '255 105 180',
			 'A Deep Commitment to Purple': '125 64 113',
			 'Noble Hatter\'s Violet': '81 56 74',
			 'A Color Similar to Slate': '47 79 79',
			 'The Bitter Taste of Defeat and Lime': '50 205 50',
			 'Indubitably Green': '114 158 66',
			 'Drably Olive': '128 128 0',
			 'Zephaniah\'s Greed': '66 79 59',
			 'Waterlogged Lab Coat (RED)': '168 154 140',
			 'Balaclavas Are Forever (RED)': '59 31 35',
			 'Team Spirit (RED)': '184 56 59',
			 'Operator\'s Overalls (RED)': '72 56 56',
			 'The Value of Teamwork (RED)': '128 48 32',
			 'An Air of Debonair (RED)': '101 71 64',
			 'Cream Spirit (RED)': '195 108 45'
			 }

BLUPaintDict = {'Stock (BLU)': 'Stock',
				'Waterlogged Lab Coat (BLU)': '131 159 163',
				'Balaclavas Are Forever (BLU)': '24 35 61',
				'Team Spirit (BLU)': '88 133 162',
				'Operator\'s Overalls (BLU)': '56 66 72',
				'The Value of Teamwork (BLU)': '37 109 141',
				'An Air of Debonair (BLU)': '40 57 77',
				'Cream Spirit (BLU)': '184 128 53'
				}

paintHexDict = {'Stock': '',
				'An Extraordinary Abundance of Tinge': 'E6E6E6',
				'Color No. 216-190-216': 'D8BED8',
				'Peculiarly Drab Tincture': 'C5AF91',
				'Aged Moustache Grey': '7E7E7E',
				'A Distinctive Lack of Hue': '141414',
				'Radigan Conagher Brown': '694D3A',
				'Ye Olde Rustic Color': 'F0E68C',
				'Muskelmannbraun': 'A57545',
				'Australium Gold': 'E7B53B',
				'The Color of a Gentlemann\'s Business Pants': 'F0E68C',
				'Dark Salmon Injustice': 'E9967A',
				'Mann Co. Orange': 'CF7336',
				'Pink as Hell': 'FF69B4',
				'A Deep Commitment to Purple': '7D4071',
				'Noble Hatter\'s Violet': '51384A',
				'A Color Similar to Slate': '2F4F4F',
				'The Bitter Taste of Defeat and Lime': '32CD32',
				'Indubitably Green': '729E42',
				'Drably Olive': '808000',
				'Zephaniah\'s Greed': '424F3B',
				'Waterlogged Lab Coat (RED)': 'A89A8C',
				'Balaclavas Are Forever (RED)': '3B1F23',
				'Team Spirit (RED)': 'B8383B',
				'Operator\'s Overalls (RED)': '483838',
				'The Value of Teamwork (RED)': '803020',
				'An Air of Debonair (RED)': '654740',
				'Cream Spirit (RED)': 'C36C2D',
				'Stock (BLU)': '',
				'Waterlogged Lab Coat (BLU)': '839FA3',
				'Balaclavas Are Forever (BLU)': '18233D',
				'Team Spirit (BLU)': '5885A2',
				'Operator\'s Overalls (BLU)': '384248',
				'The Value of Teamwork (BLU)': '256D8D',
				'An Air of Debonair (BLU)': '28394D',
				'Cream Spirit (BLU)': 'B88035'
				}

def paintHat(colour, VMTFile):
	vmt = open(VMTFile, 'rb').read()
	pattern = '"\$color2" "\{(.[^\}]+)\}"'
	regex = re.compile(pattern, re.IGNORECASE)
	if regex.search(vmt):
		if colour == 'Stock':
			pattern2 = '(\s*)"\$colortint_base" "\{(.[^\}]+)\}"'
			regex = re.compile(pattern2, re.IGNORECASE)
			result = regex.search(vmt)
			vmt = re.sub(pattern, '"$color2" "{' + result.group(2) + '}"', vmt)
		else:
			vmt = re.sub(pattern, '"$color2" "{' + colour + '}"', vmt)
	else:
		pattern = '(\s*)"\$colortint_base" "\{(.[^\}]+)\}"'
		regex = re.compile(pattern, re.IGNORECASE)
		result = regex.search(vmt)
		if colour == 'Stock':
			vmt = re.sub(pattern, result.group(1) + '"$colortint_base" "{' + result.group(2) + '}"\n' + result.group(1).replace('\r\n','') + '"$color2" "{' + result.group(2) + '}"', vmt)
		else:
			vmt = re.sub(pattern, result.group(1) + '"$colortint_base" "{' + result.group(2) + '}"\n' + result.group(1).replace('\r\n','') + '"$color2" "{' + colour + '}"', vmt)
	f = open(VMTFile, 'wb')
	f.write(vmt)
	f.close()

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

class BlendingThread(threading.Thread):
	allThreads = []
	def __init__(self, xrotation, n, blackImages, whiteImages, saveDir):
		self.xrotation = xrotation
		self.n = n
		self.blackImages = blackImages
		self.whiteImages = whiteImages
		self.saveDir = saveDir
		threading.Thread.__init__(self)
		BlendingThread.allThreads.append(self)
		self.start()
	def run(self):
		for colour in self.whiteImages:
			print 'Processing ' + colour
			if self.xrotation == -15:
				imgname = str(self.n) + 'up' + paintHexDict[colour] + '.png'
			elif self.xrotation == 15:
				imgname = str(self.n) + 'down' + paintHexDict[colour] + '.png'
			else:
				imgname = str(self.n) + '' + paintHexDict[colour] + '.png'
			black = imgpie.wrap(self.blackImages[colour])
			white = imgpie.wrap(self.whiteImages[colour])
			blended = black.blackWhiteBlend(white)
			blended.save(self.saveDir + os.sep + imgname)
	def waitForAll():
		for t in BlendingThread.allThreads:
			t.join()
	
def automateDis(model, numberOfImages=24, n=0, rotationOffset=None, initialRotation=None, initialTranslation=None, verticalOffset=None, disableXRotation=False, hatName=None, REDVMTFile=None, BLUVMTFile=None):
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
	
	# Time for user to cancel script start
	mouse.sleep(3)
	
	try:
		subprocess.Popen(['taskkill', '/f', '/t' ,'/im', 'hlmv.exe'], stdout=PIPE, stderr=PIPE)
		mouse.sleep(2)
	except:
		pass
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
				mouse.sleep(0.5)
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
				# Take whiteBG screenshots and crop
				mouse.sleep(1.5)
				def paintcycle(dict, whiteBackgroundImages, blackBackgroundImages):
					for colour in dict:
						paintHat(dict[colour], REDVMTFile)
						SendKeys("""{F5}""")
						mouse.sleep(0.1)
						imgWhiteBG = ImageGrab.grab()
						imgWhiteBG = imgWhiteBG.crop(imgCropBoundaries)
						whiteBackgroundImages[colour] = imgWhiteBG
					# Change BG colour to black
					SendKeys("""^b""")
					# Take blackBG screenshots and crop
					for colour in dict:
						paintHat(dict[colour], REDVMTFile)
						SendKeys("""{F5}""")
						mouse.sleep(0.1)
						imgBlackBG = ImageGrab.grab()
						imgBlackBG = imgBlackBG.crop(imgCropBoundaries)
						blackBackgroundImages[colour] = imgBlackBG
					SendKeys("""^b""")
					SendKeys("""{F5}""")
					return whiteBackgroundImages, blackBackgroundImages
				whiteBackgroundImages = {}
				blackBackgroundImages = {}
				whiteBackgroundImages, blackBackgroundImages = paintcycle(paintDict, whiteBackgroundImages, blackBackgroundImages)
				# Change RED hat to BLU
				redVMTContents = open(REDVMTFile, 'rb').read()
				bluVMTContents = open(BLUVMTFile, 'rb').read()
				f = open(REDVMTFile, 'wb')
				f.write(bluVMTContents)
				f.close()
				whiteBackgroundImages, blackBackgroundImages = paintcycle(BLUPaintDict, whiteBackgroundImages, blackBackgroundImages)
				g = open(REDVMTFile, 'wb')
				g.write(redVMTContents)
				g.close()
				# Remove background from images
				try:
					BlendingThread.waitForAll()
				except:
					pass
				BlendingThread(xrotation, n, blackBackgroundImages, whiteBackgroundImages, outputFolder)
				# Close HLMV
				subprocess.Popen(['taskkill', '/f', '/t' ,'/im', 'hlmv.exe'], stdout=PIPE, stderr=PIPE)
		n += 1
	BlendingThread.waitForAll()
	# Stitch images together
	print 'Stitching images together...'
	for colour in paintHexDict:
		if colour == 'Stock':
			finalImageName = hatName + ' RED ' + '3D.jpg'
		elif colour == 'Stock (BLU)':
			finalImageName = hatName + ' BLU ' + '3D.jpg'
		else:
			finalImageName = hatName + ' ' + paintHexDict[colour] + ' 3D.jpg'
		##### Need to thread this #####
		stitch(outputFolder, colour, finalImageName)
	# Upload images to wiki
	# All done yay
	print '\nAll done'

# Poot values here
model = HLMVModelRegistryKey('models.player.items.heavy.heavy_stocking_cap.mdl')
starttime = int(round(time.time()))
automateDis(model=model,
			n=0,
			rotationOffset=None,
			verticalOffset=None,
			disableXRotation=False,
			initialRotation=(0.000000, 0.000000, 0.000000),
			initialTranslation=(40.320000, 0.000000, 0.000000),
			hatName = '',
			REDVMTFile = r'E:\Steam\steamapps\moussekateer\team fortress 2\tf\materials\models\player\items\heavy\heavy_stocking_cap.vmt',
			BLUVMTFile = r'E:\Steam\steamapps\moussekateer\team fortress 2\tf\materials\models\player\items\heavy\heavy_stocking_cap_blue.vmt'
			)
print 'completed in ' + str(int(round(time.time())) - starttime) + 'seconds'