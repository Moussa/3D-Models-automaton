from mouse import click # 300
from os import sep # Various
from subprocess import Popen, PIPE # 38, 41
from math import sin, cos, pi # 29, 104, 125
from imgpie import wrap # 179, 180
from time import time, sleep # 59, 263, 481
from win32api import GetKeyState
from win32gui import EnumWindows, GetWindowText, SetForegroundWindow, ShowWindow # 44
from HLMVModel import HLMVModelRegistryKey # 486
from Stitch import stitch # 416
from SendKeys import SendKeys # Various
from screenshot import screenshot
from threadpool import threadpool
import Image
import threading
import win32con
import uploadFile
import scriptconstants
try:
	import psyco
	psyco.full()
except:
	pass

global threads
threads = []
paintDict = scriptconstants.paintDict
BLUPaintDict = scriptconstants.BLUPaintDict
paintHexDict = scriptconstants.paintHexDict

degreesToRadiansFactor = pi / 180.0
outputImagesDir = r'output' # The directory where the output images will be saved.
SDKLauncherStartingPoint = (20, 20) # Rough x, y screen coordindates of SDK Launcher. This is near the top left of the screen by default.
monitorResolution = [1920, 1080] # The monitor resolution of the user in the form of a list; [pixel width, pixel height].
imgCropBoundaries = (1, 42, 1919, 799) # The cropping boundaries, as a pixel distance from the top left corner, for the images as a tuple; (left boundary, top boundary, right boundary, bottom boundary).
fileButtonCoordindates = (14, 32) # The coordinates for the File menu button in HLMV
threadedBlending = True # Use threading for blending computations
sleepFactor = 1.0 # Sleep time factor that affects how long the script waits for HLMV to load/models to load etc

def openHLMV(pathToHlmv):
	Popen([pathToHlmv + sep + 'hlmv.exe'], stdout=PIPE, stderr=PIPE)

def closeHLMV():
	Popen(['taskkill', '/f', '/t' ,'/im', 'hlmv.exe'], stdout=PIPE, stderr=PIPE)

def prepareHLMV():
	window_list = []
	def enum_callback(hwnd, results):
		window_list.append((hwnd, GetWindowText(hwnd)))

	EnumWindows(enum_callback, [])

	handle_id = None
	for hwnd, title in window_list:
		if 'half-life model viewer' in title.lower():
			handle_id = hwnd
			break
	SetForegroundWindow(handle_id)
	ShowWindow(handle_id, win32con.SW_MAXIMIZE)

def sleep(sleeptime):

def paintHat(colour, VMTFile):
	vmt = open(VMTFile, 'rb').read()
	pattern = '"\$color2"\s+"\{(.[^\}]+)\}"'
	regex = re.compile(pattern, re.IGNORECASE)
	if regex.search(vmt):
		if colour == 'Stock':
			pattern2 = '(\s*)"\$colortint_base"\s+"\{(.[^\}]+)\}"'
			regex = re.compile(pattern2, re.IGNORECASE)
			result = regex.search(vmt)
			colour = result.group(2)
		vmt = re.sub(pattern, '"$color2" "{' + colour + '}"', vmt)
	else:
		pattern = '(\s*)"\$colortint_base"\s+"\{(.[^\}]+)\}"'
		regex = re.compile(pattern, re.IGNORECASE)
		result = regex.search(vmt)
		if colour == 'Stock':
			colour = result.group(2)
		vmt = re.sub(pattern, result.group(1) + '"$colortint_base" "{' + result.group(2) + '}"\n' + result.group(1).replace('\r\n','') + '"$color2" "{' + colour + '}"', vmt)
	f = open(VMTFile, 'wb')
	f.write(vmt)
	f.close()
	sleep(sleeptime*sleepFactor)

def getBrightness(p):
	return (299.0 * p[0] + 587.0 * p[1] + 114.0 * p[2]) / 1000.0

def blend(blackImg, whiteImg, name):
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
	blackImg.save(name, 'PNG')

def rotateAboutNewCentre(x, y, z, rotOffset, yAngle, xAngle):
	""" Method to position a model in HLMV with a new center of rotation.
	
		Parameters:
                x -> The current x position of the model.
				y -> The current y position of the model.
				z -> The current z position of the model.
				rotOffset -> The distance from the default centre of rotation to the new one (in HLMV units).
				yAngle -> The angle the model has been rotated by around the y axis, in degrees.
				xAngle -> The angle the model has been rotated by around the x axis, in degrees.
	"""
	if yAngle < 0:
		yAngle += 360 # HLMV goes -180 to 180, not 0 to 360.
	yAngle *= degreesToRadiansFactor
	xAngle *= degreesToRadiansFactor

	x += cos(yAngle) * rotOffset
	y += sin(yAngle) * rotOffset
	z -= sin(xAngle) * rotOffset
	return [x, y, z]

def offsetVertically(x, y, z, vertOffset, yAngle, xAngle):
	""" Method to position a model in HLMV with a new vertical offset
	
		Parameters:
                x -> The current x position of the model.
				y -> The current y position of the model.
				z -> The current z position of the model.
				vertOffset -> 
				yAngle -> The angle the model has been rotated by around the y axis, in degrees.
				xAngle -> The angle the model has been rotated by around the x axis, in degrees.
	"""
	if yAngle < 0:
		yAngle += 360 # HLMV goes -180 to 180, not 0 to 360.
	yAngle *= degreesToRadiansFactor
	xAngle *= degreesToRadiansFactor

	x += sin(xAngle) * (sin(yAngle) * vertOffset
	y += sin(xAngle) * (sin(yAngle) * vertOffset
	return [x, y, z]

def automateDis(model,
				numberOfImages=24,
				n=0,
				rotationOffset=None,
				initialRotation=None,
				initialTranslation=None,
				verticalOffset=None,
				verticalRotations=1,
				screenshotPause=False,
				paint=False,
				teamColours=False,
				pathToHlmv='',
				itemName='',
				REDVMTFiles=None,
				BLUVMTFiles=None,
				wikiUsername=None,
				wikiPassword=None):
	""" Method to automize process of taking images for 3D model views. 
	
		Parameters:
                model -> An instance of a HLMVModelRegistryKey object for the model. Required.
				numberOfImages -> Number of images to take for one full rotation. Optional, default is 24.
				n -> Which nth step of rotation to start at. Optional, default is 0.
				rotationOffset -> The distance from the default centre of rotation to the new one (in HLMV units). Optional, default is none.
				initialRotation -> The initial model rotation as a tuple. Optional, default is (0 0 0).
				initialTranslation -> The initial model translation as a tuple. Optional, default is (0 0 0).
				verticalOffset -> The vertical offset for models that are centered in both other planes but not vertically. Optional, default is none.
				verticalRotations -> Int number where 1 = up/down rotations and 0 = no vertical rotations. Default is 1.
				screenshotPause -> Pause on every screenshot to pose model. Press number lock key to move on once finished posing. Default is False.
				paint -> Boolean to indicate whether model is paintable. Optional, default is False.
				teamColours -> Boolean to indicate whether model is team coloured. Optional, default is False.
				pathToHlmv -> Path to hlmv.exe. Usually in common\Team Fortress 2\bin
				itemName -> The name of the item. Optional, default is blank.
				REDVMTFiles -> The RED vmt file locations. Optional, default is none.
				BLUVMTFiles -> The BLU vmt file locations. Optional, default is none.
				wikiUsername -> wiki.tf2.com username. Optional, default is none.
				wikiPassword -> wiki.tf2.com password. Optional, default is none.
	"""

	folder = raw_input('Folder name for created images: ')
	outputFolder = outputImagesDir + sep + folder
	try:
		os.makedirs(outputFolder)
	except:
		answer = raw_input('Folder already exists, overwrite files? y\\n? ')
		if answer.lower() in ['no', 'n']:
			sys.exit(1)

	if initialTranslation is None:
		initialTranslation = [model.returnTranslation()['x'], model.returnTranslation()['y'], model.returnTranslation()['z']]
	if initialRotation is None:
		initialRotation = [model.returnRotation()['x'], model.returnRotation()['y'], model.returnRotation()['z']]

	# Time for user to cancel script start
	sleep(3)

	try:
		closeHLMV()
		sleep(2.0)
	except:
		pass
	print 'initialTranslation =', initialTranslation
	print 'initialRotation =', initialRotation
	
	model.setTranslation(x = initialTranslation[0], y = initialTranslation[1], z = initialTranslation[2])
	model.setNormalMapping(True)
	model.setBGColour(255, 255, 255, 255)
	for yrotation in range((-180 + (360/numberOfImages * n)), 180, 360/numberOfImages):
		print 'n =', str(n)
		for xrotation in range(-15, 30, 15):
			if (verticalRotations == 0 and xrotation == 0) or verticalRotations == 1:
				# Set rotation
				sleep(0.5)
				model.setRotation(x = xrotation + float(initialRotation[0]), y = yrotation + float(initialRotation[1]), z = initialRotation[2])
				print 'xRot = {0}, yRot = {1}'.format(xrotation, yrotation)
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
				# Open HLMV
				openHLMV(pathToHlmv)
				sleep(2)
				# Focus and maximise HLMV
				prepareHLMV()
				# Open recent model
				click(x=fileButtonCoordindates[0],y=fileButtonCoordindates[1])
				SendKeys(r'{DOWN 10}{RIGHT}{ENTER}')
				sleep(1)
				# If user wants to pose model before taking screenshot, make script wait
				if screenshotPause:
					numKeyState = GetKeyState(win32con.VK_NUMLOCK)
					while GetKeyState(win32con.VK_NUMLOCK) == numKeyState:
						pass
				# Item painting method
				def paintcycle(dict, whiteBackgroundImages, blackBackgroundImages):
					# Take whiteBG screenshots and crop
					for colour in dict:
						paintHat(dict[colour], REDVMTFiles)
						SendKeys(r'{F5}')
						sleep(1.0)
						imgWhiteBG = screenshot().crop(imgCropBoundaries)
						whiteBackgroundImages[colour] = imgWhiteBG
					# Change BG colour to black
					SendKeys(r'^b')
					# Take blackBG screenshots and crop
					for colour in dict:
						paintHat(dict[colour], REDVMTFiles)
						SendKeys(r'{F5}')
						sleep(1.0)
						imgBlackBG = screenshot().crop(imgCropBoundaries)
						blackBackgroundImages[colour] = imgBlackBG
					SendKeys(r'^b')
					SendKeys(r'{F5}')
					return whiteBackgroundImages, blackBackgroundImages
				if paint:
					whiteBackgroundImages = {}
					blackBackgroundImages = {}
					whiteBackgroundImages, blackBackgroundImages = paintcycle(paintDict, whiteBackgroundImages, blackBackgroundImages)
					if teamColours:
						# Change RED hat to BLU
						redFiles = []
						bluFiles = []
						for fileName in REDVMTFiles:
							redFiles.append(open(fileName, 'rb').read())
						for fileName in BLUVMTFiles:
							bluFiles.append(open(fileName, 'rb').read())
						for file, fileName in zip(bluFiles, redFileNames):
							with open(fileName, 'wb') as f:
								f.write(file)
						whiteBackgroundImages, blackBackgroundImages = paintcycle(BLUPaintDict, whiteBackgroundImages, blackBackgroundImages)
						for file, fileName in zip(bluFiles, redFileNames):
							with open(fileName, 'wb') as f:
								f.write(file)
					else:
						whiteBackgroundImages, blackBackgroundImages = paintcycle(BLUPaintDict, whiteBackgroundImages, blackBackgroundImages)
				else:
					if teamColours:
						# Take whiteBG screenshot and crop
						imgWhiteBGRED = screenshot().crop(imgCropBoundaries)
						# Change BG colour to black
						SendKeys(r'^b')
						# Take blackBG screenshot and crop
						imgBlackBGRED = screenshot().crop(imgCropBoundaries)
						# Change BG colour to white
						SendKeys(r'^b')
						# Change weapon colour to BLU
						redFiles = []
						bluFiles = []
						for fileName in REDVMTFiles:
							redFiles.append(open(fileName, 'rb').read())
						for fileName in BLUVMTFiles:
							bluFiles.append(open(fileName, 'rb').read())
						for file, fileName in zip(bluFiles, redFileNames):
							with open(fileName, 'wb') as f:
								f.write(file)
						SendKeys(r'{F5}')
						sleep(1.0)
						# Take whiteBG screenshot and crop
						imgWhiteBGBLU = screenshot().crop(imgCropBoundaries)
						# Change BG colour to black
						SendKeys(r'^b')
						# Take blackBG screenshot and crop
						imgBlackBGBLU = screenshot().crop(imgCropBoundaries)
						# Return VMT back to RED
						for file, fileName in zip(bluFiles, redFileNames):
							with open(fileName, 'wb') as f:
								f.write(file)
					else:
						# Take whiteBG screenshot and crop
						imgWhiteBG = screenshot().crop(imgCropBoundaries)
						# Change BG colour to black
						SendKeys(r'^b')
						# Take blackBG screenshot and crop
						imgBlackBG = screenshot().crop(imgCropBoundaries)
				# Remove background from images
				global threads
				if paint:
					for colour in whiteBackgroundImages:
						thread = Thread(target=blend, kwargs={
							'blackImg': blackBackgroundImages[colour],
							'whiteImg': whiteBackgroundImages[colour],
							'name': '%s\%d_%d_%s.png' % (outputFolder, n, xrotation / -15, paintHexDict[colour])
						})
						threads.append(thread)
						thread.start()
				elif teamColours:
					thread = Thread(target=blend, kwargs={
						'blackImg': imgBlackBGRED,
						'whiteImg': imgWhiteBGRED,
						'name': '%s\%d_%d_RED.png' % (outputFolder, n, xrotation / -15)
					})
					threads.append(thread)
					thread.start()
					thread = Thread(target=blend, kwargs={
						'blackImg': imgBlackBGBLU,
						'whiteImg': imgWhiteBGBLU,
						'name': '%s\%d_%d_BLU.png' % (outputFolder, n, xrotation / -15)
					})
					threads.append(thread)
					thread.start()
				else:
					thread = Thread(target=blend, kwargs={
						'blackImg': imgBlackBG,
						'whiteImg': imgWhiteBG,
						'name': '%s\%d_%d' % (outputFolder, n, xrotation / -15)
					})
					threads.append(thread)
					thread.start()
				# Close HLMV
				closeHLMV()
				# Check for kill switch
				killKeyState = GetKeyState(win32con.VK_CAPITAL)
				if killKeyState in [1, -127]:
					print 'Successfully terminated'
					sys.exit(0)
		n += 1
	for thread in threads:
		thread.join() # Wait for threads to finish, if any
	# Stitch images together
	print 'Stitching images together...'
	stitchPool = threadpool(numThreads=2, defaultTarget=stitch)
	if paint:
		for colour in paintHexDict:
			if colour == 'Stock':
				if teamColours:
					finalImageName = itemName + ' RED 3D.jpg'
				else:
					finalImageName = itemName + ' 3D.jpg'
			elif colour == 'Stock (BLU)':
				if teamColours:
					finalImageName = itemName + ' BLU 3D.jpg'
			else:
				finalImageName = '{0} {1} 3D.jpg'.format(itemName, paintHexDict[colour])
			##### Need to thread this #####
			if colour != 'Stock (BLU)' or teamColours:
				stitchPool(outputFolder, paintHexDict[colour], finalImageName, numberOfImages, verticalRotations)
	else:
		if teamColours:
			finalREDImageName = itemName + ' RED 3D.jpg'
			finalBLUImageName = itemName + ' BLU 3D.jpg'
			stitchPool(outputFolder, 'RED', finalREDImageName, numberOfImages, verticalRotations)
			stitchPool(outputFolder, 'BLU', finalBLUImageName, numberOfImages, verticalRotations)
		else:
			finalImageName = itemName + ' 3D.jpg'
			stitchPool(outputFolder, None, finalImageName, numberOfImages, verticalRotations)
	stitchPool.shutdown()
	# Upload images to wiki
	if paint:
		for colour in paintHexDict:
			if colour == 'Stock':
				if teamColours:
					fileName = itemName + ' RED 3D.jpg'
				else:
					fileName = itemName + ' 3D.jpg'
			elif colour == 'Stock (BLU)':
				if teamColours:
					fileName = itemName + ' BLU 3D.jpg'
			else:
				fileName = '{0} {1} 3D.jpg'.format(itemName, paintHexDict[colour])
			url = uploadFile.fileURL(fileName)
			description = open(outputFolder + sep + fileName + ' offsetmap.txt', 'rb').read()
			description = description.replace('url = <nowiki></nowiki>', 'url = <nowiki>' + url + '</nowiki>')
			if colour != 'Stock (BLU)' or teamColours:
				uploadFile.uploadFile(outputFolder + sep + fileName, fileName, description, wikiUsername, wikiPassword, category='', overwrite=False)
	else:
		if teamColours:
			finalREDImageName = itemName + ' RED 3D.jpg'
			finalBLUImageName = itemName + ' BLU 3D.jpg'
			url = uploadFile.fileURL(finalREDImageName)
			url2 = uploadFile.fileURL(finalBLUImageName)
			description = open(outputFolder + sep + finalREDImageName + ' offsetmap.txt', 'rb').read()
			description = description.replace('url = <nowiki></nowiki>','url = <nowiki>' + url + '</nowiki>')
			description2 = open(outputFolder + sep + finalBLUImageName + ' offsetmap.txt', 'rb').read()
			description2 = description2.replace('url = <nowiki></nowiki>','url = <nowiki>' + url2 + '</nowiki>')
			uploadFile.uploadFile(outputFolder + sep + finalREDImageName, finalREDImageName, description, wikiUsername, wikiPassword, category='', overwrite=False)
			uploadFile.uploadFile(outputFolder + sep + finalBLUImageName, finalBLUImageName, description2, wikiUsername, wikiPassword, category='', overwrite=False)
		else:
			finalImageName = itemName + ' 3D.jpg'
			url = uploadFile.fileURL(finalImageName)
			description = open(outputFolder + sep + finalImageName + ' offsetmap.txt', 'rb').read()
			description = description.replace('url = <nowiki></nowiki>','url = <nowiki>' + url + '</nowiki>')
			uploadFile.uploadFile(outputFolder + sep + finalImageName, finalImageName, description, wikiUsername, wikiPassword, category='', overwrite=False)
	# All done yay
	print '\nAll done'

if __name__ == '__main__':
	# Poot values here
	starttime = time()
	
	# Example usage
	model = HLMVModelRegistryKey('models.player.items.heavy.heavy_stocking_cap.mdl')
	automateDis(model = model,
				numberOfImages = 24,
				n = 0,
				rotationOffset = None,
				verticalOffset = None,
				verticalRotations = 1,
				screenshotPause = False,
				initialRotation = (0.000000, 0.000000, 0.000000),
				initialTranslation = (40.320000, 0.000000, 0.000000),
				paint = True,
				teamColours = True,
				pathToHlmv = r'F:\Steam\steamapps\common\Team Fortress 2\bin',
				itemName = 'User Moussekateer Test',
				REDVMTFiles = [r'E:\Steam\steamapps\moussekateer\team fortress 2\tf\materials\models\player\items\heavy\heavy_stocking_cap.vmt'],
				BLUVMTFiles = [r'E:\Steam\steamapps\moussekateer\team fortress 2\tf\materials\models\player\items\heavy\heavy_stocking_cap_blue.vmt'],
				wikiPassword = 'lolno'
				wikiUsername = 'Moussekateer',
				)

	print 'completed in ' + str(int(time() - starttime)) + 'seconds'
