from hashlib import md5 # 34
from HLMVModel import HLMVModelRegistryKey # 298
from PIL.ImageGrab import grab # Various
from os import makedirs, sep # Various
from subprocess import Popen, PIPE # 166, 193, 265
from time import time, sleep # Various, 296, 316
from imageprocessor import imageProcessor # Various
from SendKeys import SendKeys # Various
from threading import Thread # 226, 257
from wikitools import wiki # 30
from wikitools.wikifile import File # 38
from wikitools.page import Page # 38
from win32api import GetKeyState, mouse_event, SetCursorPos
import win32con
from win32gui import EnumWindows, GetWindowText, SetForegroundWindow, ShowWindow # 195-199
try:
    import psyco
    psyco.full()
except:
    pass

global threads
threads = [] # Used to track the threads used for blending
wiki = wiki.Wiki('http://wiki.teamfortress.com/w/api.php')
outputImagesDir = r'output' # The directory where the output images will be saved.
# The cropping boundaries, as a pixel
# distance from the top left corner, for the images as a tuple:
# (left boundary, top boundary, right boundary, bottom boundary).
imgCropBoundaries = (1, 42, 1279, 510)
fileButtonCoordindates = (14, 32) # The coordinates for the File menu button in HLMV
#sleepFactor = 1.0 # Multiplicitive factor for script wait times

def uploadFile(outputFolder, title):
    if not wiki.isLoggedIn():
        return
    hash = md5(title.replace(' ', '_')).hexdigest()
    url = 'http://wiki.teamfortress.com/w/images/%s/%s/%s' % (hash[:1], hash[:2], title.replace(' ', '_'))
    file = open('%s\\%s' % (outputFolder, title), 'rb')
    description = open('%s\\%s offsetmap.txt' % (outputFolder, title), 'rb').read()
    description = description.replace('url = <nowiki></nowiki>', 'url = <nowiki>' + url + '</nowiki>')

    print 'Uploading', title, '...'
    target = File(wiki, title)
    if target.exists:
        answer = raw_input('File already exists, ovewrite? y\\n? ')
        ignorewarnings = answer.lower() in ['yes', 'y']
        res = target.upload(file, ignorewarnings=ignorewarnings)
        if res['upload']['result'] == 'Warning':
            print 'Failed for file:', title
            print res['upload']['warnings']
        else:
            Page(wiki, 'File:'+title).edit(text=description, redirect=False)
    else:
        res = target.upload(file, comment=description)
        if res['upload']['result'] == 'Warning':
            print 'Failed for file: ', title
            print res['upload']['warnings']

def automateDis(
    key,
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
    BLUVMTFiles=None):
    """
    Method to automize process of taking images for 3D model views. 
    
    Parameters:
        key -> (REQUIRED) The registry key for the model
        numberOfImages -> Number of images to take per one full rotation.
        n -> Offset the rotation from this image number.
        rotationOffset -> Offset the center of rotation horizontally
        verticalOffset -> Offset the center of rotation vertically
        verticalRotations -> Set to 0 to disable vertical rotations.
        screenshotPause -> Pause on each screenshot. NUMLOCK will continue.
        pathToHlmv -> Path to hlmv.exe. Usually in common\Team Fortress 2\bin
        itemName -> The name of the item, as will be saved to disk and uploaded
        REDVMTFiles -> A list of RED vmt file locations.
        BLUVMTFiles -> A list of BLU vmt file locations.
    """

    outputFolder = outputImagesDir + sep + itemName
    try:
        makedirs(outputFolder)
    except WindowsError:
        answer = raw_input('Folder "%s" already exists, overwrite files? (y\\n) ' % itemName)
        if answer.lower() in ['no', 'n']:
            import sys
            sys.exit(1)

    # Time for user to cancel script start
    sleep(3)

    # Close HLMV, in case it's already open. Suppress all responses.
    model = HLMVModelRegistryKey(key, rotation=initialRotation, translation=initialTranslation)

    Popen(['taskkill', '/f', '/t', '/im', 'hlmv.exe'], stderr=PIPE, stdout=PIPE)
    sleep(2.0)
    print 'initialTranslation =', initialTranslation
    print 'initialRotation =', initialRotation
    
    # Adjust model rotation as needed
    if rotationOffset:
        model.rot_offset = rotationOffset
    if verticalOffset:
        model.vert_offset = verticalOffset

    # Create the image processors, used for blending, cropping, and stitching
    if teamColours:
        ipRed = imageProcessor(suffix='RED')
        ipBlu = imageProcessor(suffix='BLU')
    else:
        ip = imageProcessor()

    for y in range(n, numberOfImages):
        yrotation = (360/numberOfImages)*y
        print 'n =', n
        for xrotation in range(15, -30, -15):
            if (verticalRotations == 0 and xrotation == 0) or verticalRotations == 1:
                # Set rotation
                sleep(0.5)
                model.rotate(xrotation, yrotation)
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
                if teamColours:
                    # Take two (red) images, on one black and one on white, blend them together to find transparency
                    imgWhiteBG = grab().crop(imgCropBoundaries)
                    SendKeys(r'^b')
                    imgBlackBG = grab().crop(imgCropBoundaries)
                    SendKeys(r'^b')
                    thread = Thread(target=ipRed.blend, kwargs={
                        'blackImg': imgBlackBG,
                        'whiteImg': imgWhiteBG,
                        'name': '%s\%d_%d_RED.png' % (outputFolder, n, xrotation / -15)
                    })
                    threads.append(thread)
                    thread.start()
                    
                    # Swap the red and blue .vmts to change the weapon's colour
                    redFiles = [open(f, 'rb').read() for f in REDVMTFiles]
                    for bluFileName, redFileName in zip(BLUVMTFiles, REDVMTFiles):
                        with open(redFileName, 'wb') as redFile, open(bluFileName, 'rb') as bluFile:
                            redFile.write(bluFile.read())
                    SendKeys(r'{F5}')
                    sleep(1.0)

                    # Take two (blue) images and blend them together
                    imgWhiteBG = grab().crop(imgCropBoundaries)
                    SendKeys(r'^b')
                    imgBlackBG = grab().crop(imgCropBoundaries)
                    SendKeys(r'^b')
                    thread = Thread(target=ipBlu.blend, kwargs={
                        'blackImg': imgBlackBG,
                        'whiteImg': imgWhiteBG,
                        'name': '%s\%d_%d_BLU.png' % (outputFolder, n, xrotation / -15)
                    })
                    threads.append(thread)
                    thread.start()

                    # Swap the item back to red
                    for redFileName, redFileContents in zip(REDVMTFiles, redFiles):
                        with open(redFileName, 'wb') as redFile:
                            redFile.write(redFileContents)
                else:
                    # Take two images, on one black and one on white, blend them together to find transparency
                    imgWhiteBG = grab().crop(imgCropBoundaries)
                    SendKeys(r'^b')
                    imgBlackBG = grab().crop(imgCropBoundaries)
                    SendKeys(r'^b')
                    thread = Thread(target=ip.blend, kwargs={
                        'blackImg': imgBlackBG,
                        'whiteImg': imgWhiteBG,
                        'name': '%s\%d_%d.png' % (outputFolder, n, xrotation / -15)
                    })
                    threads.append(thread)
                    thread.start()
                # Close HLMV, supress success message
                Popen(['taskkill', '/f', '/t' ,'/im', 'hlmv.exe'], stdout=PIPE)
                # Check for kill switch
                if GetKeyState(win32con.VK_CAPITAL) in [1, -127]:
                    print 'Successfully terminated'
                    import sys
                    sys.exit(0)
        n += 1
    for thread in threads:
        thread.join() # Wait for threads to finish, if any
    print 'Stitching images together...'
    if teamColours:
        ipRed.stitch(outputFolder + sep + itemName + ' RED 3D.jpg', n, verticalRotations)
        ipBlu.stitch(outputFolder + sep + itemName + ' BLU 3D.jpg', n, verticalRotations)
    else:
        ip.stitch(outputFolder + sep + itemName + ' 3D.jpg', n, verticalRotations)
    # Upload images to wiki
    if teamColours:
        uploadFile(outputFolder, itemName + ' RED 3D.jpg')
        uploadFile(outputFolder, itemName + ' BLU 3D.jpg')
    else:
        uploadFile(outputFolder, itemName + ' 3D.jpg')
    # All done yay
    print '\nAll done'

if __name__ == '__main__':
    #wiki.login('darkid')
    starttime = time()
    
    # Poot values here
    automateDis(key = 'models.workshop.weapons.c_models.c_atom_launcher.c_atom_launcher.mdl',
                numberOfImages = 24,
                n = 0,
                rotationOffset = -6,
                verticalOffset = None,
                initialRotation = (0.000000, 0.000000, 0.000000),
                initialTranslation = (79.149429, 0.000000, 1.789900),
                verticalRotations = 0,
                screenshotPause = False,
                teamColours = False,
                pathToHlmv = r'F:\Steam\steamapps\common\Team Fortress 2\bin',
                itemName = 'User Darkid Test',
                #REDVMTFiles = [r'F:\Steam\steamapps\common\Team Fortress 2\tf\custom\MatOverrides\materials\models\workshop\weapons\c_models\c_invasion_wrangler\c_invasion_wrangler.vmt', r'F:\Steam\steamapps\common\Team Fortress 2\tf\custom\MatOverrides\materials\models\workshop\weapons\c_models\c_invasion_wrangler\c_invasion_wrangler_laser.vmt'],
                #BLUVMTFiles = [r'F:\Steam\steamapps\common\Team Fortress 2\tf\custom\MatOverrides\materials\models\workshop\weapons\c_models\c_invasion_wrangler\c_invasion_wrangler_blue.vmt', r'F:\Steam\steamapps\common\Team Fortress 2\tf\custom\MatOverrides\materials\models\workshop\weapons\c_models\c_invasion_wrangler\c_invasion_wrangler_laser_blue.vmt'],
                )

    print 'completed in', int(time() - starttime), 'seconds'
