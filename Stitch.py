import os, Image, ImageFile, numpy
from threading import Thread
try:
	import psyco
	psyco.full()
except:
	pass

targetDimension = 280
targetSize = 512 * 1024 # 512 KB
global maxFrameSize, finalSize, minCrop, cropped, crops
maxFrameSize = [0, 0]
finalSize = (0, 0)
minCrop = [999999, 999999, 999999, 999999]
cropped = []
crops = {}
_imageDtype = numpy.dtype('i')

# Finds the closest-cropped lines that are all white.
def cropTask(n, filename):
	img = Image.open(filename).convert('RGBA')
	alpha = numpy.array(img, dtype=_imageDtype)[:,:,3]
	horizontal = alpha.any(axis=0).nonzero()[0]
	vertical = alpha.any(axis=1).nonzero()[0]
	cropping = (horizontal[0], vertical[0], horizontal[-1], vertical[-1])
	global maxFrameSize, finalSize, minCrop, cropped, crops
	size = img.size[:]
	newI = img.crop(cropping)
	if size[0] > maxFrameSize[0]:
		maxFrameSize[0] = size[0]
	if size[1] > maxFrameSize[1]:
		maxFrameSize[1] = size[1]
	cropped[n].append(newI)
	crops[newI] = cropping
	finalSize[0] += newI.size[0]
	finalSize[1] = max(finalSize[1], newI.size[1] + cropping[1])
	if cropping[0] < minCrop[0]:
		minCrop[0] = cropping[0]
	if cropping[1] < minCrop[1]:
		minCrop[1] = cropping[1]
	if size[0] - cropping[2] < minCrop[2]:
		minCrop[2] = size[0] - cropping[2]
	if size[1] - cropping[3] < minCrop[3]:
		minCrop[3] = size[1] - cropping[3]

def stitch(imagesDir, outpootFile, yRotNum, xRotNum=1):
	global maxFrameSize, minCrop, cropped, crops, finalSize
	outpootFile = imagesDir + os.sep + outpootFile
	print 'Cropping frames...'
	threads = []
	n = 0
	for i in range(yRotNum):
		for s in range(-xRotNum, xRotNum + 1):
			thread = Thread(target=cropTask, kwargs={
				'n': n,
				'filename': '%s\%d_%d.png' % (imagesDir, i, s)
			})
			cropped.append(None)
			n += 1
			thread.start()
			threads.append(thread)
	for thread in threads:
		thread.join()
	print 'Minimum crop size:', minCrop
	maxFrameSize = (maxFrameSize[0] - minCrop[0] - minCrop[2], maxFrameSize[1] - minCrop[1] - minCrop[3])
	print 'Max frame size, including cropped area:', maxFrameSize
	targetRatio = float(targetDimension) / float(max(maxFrameSize))
	print 'Target scaling ratio:', targetRatio
	rescaledMaxSize = (int(maxFrameSize[0] * targetRatio), int(maxFrameSize[1] * targetRatio))
	print 'Computing rescaled sizes, and scaling...'
	finalSize[0] = int(finalSize[0]*targetRatio + (n-1)) # n-1 because 1 pixel gap between each image.
	finalSize[1] = int((finalSize[1] - minCrop[1])*targetRatio)

	fullImg = Image.new('RGBA', finalSize, (255, ) * 4)
	currentOffset = 0
	offsetMap = []
	currentOffsetIntervaled = 0
	print 'Building final image.'
	for f in cropped:
		newSize = (int(f.size[0] * targetRatio), int(f.size[1] * targetRatio))
		resImg = f.resize(newSize, Image.ANTIALIAS)
		normalizedLeftCrop = int((crops[f][0] - minCrop[0]) * targetRatio)
		normalizedTopCrop = int((crops[f][1] - minCrop[1]) * targetRatio)
		fullImg.paste(resImg, (currentOffsetIntervaled, normalizedTopCrop), resImg)
		offsetMap += [currentOffset, resImg.size[1], normalizedLeftCrop]
		currentOffset += resImg.size[0]
		currentOffsetIntervaled += resImg.size[0] + 1
	# Saving
	print 'Done, saving final image to', outpootFile
	if os.path.exists(outpootFile):
		os.remove(outpootFile)
	ImageFile.MAXBLOCK = finalSize[0] * finalSize[1] * 8 # Make sure there is enough allocated space to save the image as progressive
	quality = 101
	while not os.path.exists(outpootFile) or os.stat(outpootFile).st_size > targetSize:
		quality -= 1
		fullImg.save(outpootFile, 'JPEG', quality=quality, optimize=True, progressive=True)
	print 'Saved to', outpootFile, 'with quality', quality
	h = open(outpootFile + ' offsetmap.txt', 'wb')
	h.write('''{{#switch: {{{1|}}}
  | url = <nowiki></nowiki>
  | map = \n%d,%d,%d,%d,%s
  | height = %d
  | startframe = 16
}}<noinclude>{{3D viewer}}[[Category:3D model images]]
{{Externally linked}}''' % (currentOffset, rescaledMaxSize[0], finalSize[1], xRotNum*2 + 1, ','.join([str(o) for o in offsetMap]), targetDimension))
	h.close()
	print 'Offset map saved to ' + outpootFile + ' offsetmap.txt'
	