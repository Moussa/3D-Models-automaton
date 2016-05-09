from hashlib import md5 # 34
from HLMVModel import HLMVModelRegistryKey # 298
from ImageGrab import grab # Various
from math import cos, pi, sin # 25, 70, 91
from os import makedirs, sep # Various, 
from subprocess import Popen, PIPE # 166, 193, 265
from time import time, sleep # Various, 296, 316
from Stitch import stitch # 275
from SendKeys import SendKeys # Various
from threadpool import threadpool # 275
from threading import Thread # 226, 257
from wikitools import wiki # 30
from wikitools.wikifile import File # 38
from win32api import GetKeyState, mouse_event, SetCursorPos # 
import win32con
from win32gui import EnumWindows, GetWindowText, SetForegroundWindow, ShowWindow # 195-199
try:
	import psyco
	psyco.full()
except:
	pass

global threads
threads = [] # Used to track the threads used for blending
degreesToRadiansFactor = pi / 180.0
outputImagesDir = r'output' # The directory where the output images will be saved.
imgCropBoundaries = (1, 42, 1279, 515) # The cropping boundaries, as a pixel distance from the top left corner, for the images as a tuple; (left boundary, top boundary, right boundary, bottom boundary).
fileButtonCoordindates = (14, 32) # The coordinates for the File menu button in HLMV
#sleepFactor = 1.0 # Sleep time factor that affects how long the script waits for HLMV to load/models to load etc
wiki = wiki.Wiki('http://wiki.teamfortress.com/w/api.php')

def uploadFile(outputFolder, title):
	hash = md5(title.replace(' ', '_')).hexdigest()
	url = 'http://wiki.teamfortress.com/w/images/%s/%s/%s' % (hash[:1], hash[:2], title.replace(' ', '_'))
	description = open('%s\\%s offsetmap.txt' % (outputFolder, title), 'rb').read()
	description = description.replace('url = <nowiki></nowiki>','url = <nowiki>' + url + '</nowiki>')

	target = File(wiki, title)
	ignorewarnings = False
	if target.exists:
		answer = raw_input('File already exists, ovewrite?  y\\n? ')
		if answer.lower() in ['yes', 'y']:
			ignorewarnings = True		
	print 'Uploading', file, 'as', title, '...'
	res = target.upload(file, text=description, ignorewarnings=ignorewarnings)
	if res['upload']['result'] == 'Warning':
		print 'Failed for file: ', file
		print res['upload']['message']

def getBrightness(p):
	return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

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

	x += sin(xAngle) * sin(yAngle) * vertOffset
	y += sin(xAngle) * sin(yAngle) * vertOffset
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
				pathToHlmv -> Path to hlmv.exe. Usually in common\Team Fortress 2\bin
				itemName -> The name of the item. Optional, default is blank.
				REDVMTFiles -> The RED vmt file locations. Optional, default is none.
				BLUVMTFiles -> The BLU vmt file locations. Optional, default is none.
	"""

	folder = raw_input('Folder name for created images: ')
	outputFolder = outputImagesDir + sep + folder
	try:
		makedirs(outputFolder)
	except WindowsError:
		answer = raw_input('Folder already exists, overwrite files? y\\n? ')
		if answer.lower() in ['no', 'n']:
			import sys
			sys.exit(1)

	# Load initial translation and rotation from regedit if not otherwise provided.
	if initialTranslation is None:
		initialTranslation = [model.returnTranslation()['x'], model.returnTranslation()['y'], model.returnTranslation()['z']]
	if initialRotation is None:
		initialRotation = [model.returnRotation()['x'], model.returnRotation()['y'], model.returnRotation()['z']]

	# Time for user to cancel script start
	sleep(3)

	# Close HLMV, in case it's already open. Suppress all responses.
	Popen(['taskkill', '/f', '/t' ,'/im', 'hlmv.exe'], stderr=PIPE, stdout=PIPE)
	sleep(2.0)
	print 'initialTranslation =', initialTranslation
	print 'initialRotation =', initialRotation
	
	model.setTranslation(x = initialTranslation[0], y = initialTranslation[1], z = initialTranslation[2])
	model.setNormalMapping(True)
	model.setBGColour(255, 255, 255, 255)
	for yrotation in range((-180 + (360/numberOfImages * n)), 180, 360/numberOfImages):
		print 'n =', n
		for xrotation in range(-15, 30, 15):
			if (verticalRotations == 0 and xrotation == 0) or verticalRotations == 1:
				# Set rotation
				sleep(0.5)
				model.setRotation(x = xrotation + float(initialRotation[0]), y = yrotation + float(initialRotation[1]), z = initialRotation[2])
				print 'xRot =', xrotation, 'yRot =', yrotation
				if rotationOffset:
					# Set translation to account for off centre rotation
					result = rotateAboutNewCentre(initialTranslation[0], initialTranslation[1], initialTranslation[2], rotationOffset, yrotation, xrotation)
					print 'translation =', result
					model.setTranslation(x = result[0], y = result[1], z = result[2])
					# Set translation to account for off centre horizontal rotation
				elif verticalOffset:
					result = offsetVertically(initialTranslation[0], initialTranslation[1], initialTranslation[2], verticalOffset, yrotation, xrotation)
					print 'translation =', result
					model.setTranslation(x = result[0], y = result[1], z = result[2])
				# Open HLMV
				Popen([pathToHlmv + sep + 'hlmv.exe', '-game', pathToHlmv[:-4]+'\\tf\\'])
				sleep(2)
				# Focus and maximise HLMV
				def enum_callback(hwnd, results):
					if GetWindowText(hwnd)[:22] == 'Half-Life Model Viewer':
						SetForegroundWindow(hwnd)
						ShowWindow(hwnd, win32con.SW_MAXIMIZE)
				EnumWindows(enum_callback, [])
				# Open most recent model
				x, y = fileButtonCoordindates
				SetCursorPos((x,y))
				mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
				mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
				SendKeys(r'{UP 2}{RIGHT}{ENTER}')
				sleep(1)
				# If user wants to pose model before taking screenshot, make script wait
				if screenshotPause:
					numKeyState = GetKeyState(win32con.VK_NUMLOCK)
					while GetKeyState(win32con.VK_NUMLOCK) == numKeyState:
						pass

				global threads
				# Take whiteBG screenshot and crop
				imgWhiteBG = grab().crop(imgCropBoundaries)
				# Change BG colour to black
				SendKeys(r'^b')
				# Take blackBG screenshot and crop
				imgBlackBG = grab().crop(imgCropBoundaries)
				if teamColours:
					name = '%s\%d_%d_RED.png' % (outputFolder, n, xrotation / -15)
				else:
					name = '%s\%d_%d.png' % (outputFolder, n, xrotation / -15)
				# Remove background from images
				thread = Thread(target=blend, kwargs={
					'blackImg': imgBlackBG,
					'whiteImg': imgWhiteBG,
					'name': name
				})
				threads.append(thread)
				thread.start()
				if teamColours:
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
					imgWhiteBG = grab().crop(imgCropBoundaries)
					# Change BG colour to black
					SendKeys(r'^b')
					# Take blackBG screenshot and crop
					imgBlackBG = grab().crop(imgCropBoundaries)
					# Return VMT back to RED
					for file, fileName in zip(bluFiles, redFileNames):
						with open(fileName, 'wb') as f:
							f.write(file)
					# Remove background from images
					thread = Thread(target=blend, kwargs={
						'blackImg': imgBlackBG,
						'whiteImg': imgWhiteBG,
						'name': '%s\%d_%d_BLU.png' % (outputFolder, n, xrotation / -15)
					})
					threads.append(thread)
					thread.start()
				# Close HLMV
				Popen(['taskkill', '/f', '/t' ,'/im', 'hlmv.exe'], stderr=PIPE)
				# Check for kill switch
				if GetKeyState(win32con.VK_CAPITAL) in [1, -127]:
					print 'Successfully terminated'
					sys.exit(0)
		n += 1
	for thread in threads:
		thread.join() # Wait for threads to finish, if any
	# Stitch images together
	print 'Stitching images together...'
	stitchPool = threadpool(numThreads=2, defaultTarget=stitch)
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
	if teamColours:
		uploadFile(outputFolder, itemName + ' RED 3D.jpg')
		uploadFile(outputFolder, itemName + ' BLU 3D.jpg')
	else:
		uploadFile(outputFolder, itemName + ' 3D.jpg')
	# All done yay
	print '\nAll done'

if __name__ == '__main__':
	wiki.login('darkid')
	starttime = time()
	
	# Poot values here
	model = HLMVModelRegistryKey('models.weapons.c_models.urinejar.mdl')
	automateDis(model = model,
				numberOfImages = 6,
				n = 0,
				rotationOffset = None,
				verticalOffset = None,
				verticalRotations = 0,
				screenshotPause = False,
#				initialRotation = (0.000000, 0.000000, 0.000000),
#				initialTranslation = (30.055614, 0.000000, 1.605678),
				teamColours = False,
				pathToHlmv = r'F:\Steam\steamapps\common\Team Fortress 2\bin',
				itemName = 'User Darkid Test',
				REDVMTFiles = [],#r'F:\Steam\steamapps\common\team fortress 2\tf\materials\models\player\items\heavy\heavy_stocking_cap.vmt'],
				BLUVMTFiles = [],#r'F:\Steam\steamapps\common\team fortress 2\tf\materials\models\player\items\heavy\heavy_stocking_cap_blue.vmt'],
				)

	print 'completed in', int(time() - starttime), 'seconds'
