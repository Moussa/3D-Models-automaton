import os, Image, ImageFile, sys, threading
try:
	import psyco
	psyco.full()
except:
	pass

targetDimension = 280
targetSize = 512 * 1024 # 512 KB

from autocrop import autocrop
import threadpool

def cropTask(i, s, filename):
	# print 'Processing:', filename
	img = Image.open(filename).convert('RGBA')
	newI, cropping = autocrop(img)
	return i, s, img.size[:], newI, cropping

def stitch(imagesDir, colour, outpootFile, yRotNum, xRotNum=1):
	outpootFile = imagesDir + os.sep + outpootFile
	print 'Cropping frames...'
	fullDimensions = (0, 0)
	maxFrameSize = (None, None)
	cropped = []
	croppedNames = {}
	crops = {}
	minLeftCrop = None
	minTopCrop = None
	minRightCrop = None
	minBottomCrop = None
	# This pool should NOT use multiprocessing in order to avoid copying huge image objects around from process to process
	cropPool = threadpool.threadpool(numThreads=6, defaultTarget=cropTask, multiprocess=False)
	for i in xrange(yRotNum):
		for s in xrange(-xRotNum, xRotNum + 1):
			filename = imagesDir + os.sep + str(i) + '_' + str(s) + '.png'
			cropPool(i, s, filename)
	results = cropPool.shutdown()
	orderedResults = {}
	for result in results:
		if result['exception'] is not None:
			raise result['exception']
		i, s, size, newI, cropping = result['result']
		orderedResults[(i, s)] = (size, newI, cropping)
	for i in xrange(yRotNum):
		for s in xrange(-xRotNum, xRotNum + 1):
			size, newI, cropping = orderedResults[(i, s)]
			maxFrameSize = (max(maxFrameSize[0], size[0]), max(maxFrameSize[1], size[1]))
			cropped.append(newI)
			croppedNames[newI] = filename
			crops[newI] = cropping
			if minLeftCrop is None or cropping[0] < minLeftCrop:
				minLeftCrop = cropping[0]
			if minTopCrop is None or cropping[1] < minTopCrop:
				minTopCrop = cropping[1]
			rightCrop = size[0] - cropping[2]
			if minRightCrop is None or rightCrop < minRightCrop:
				minRightCrop = rightCrop
			bottomCrop = size[1] - cropping[3]
			if minBottomCrop is None or bottomCrop < minBottomCrop:
				minBottomCrop = bottomCrop
			fullDimensions = (fullDimensions[0] + newI.size[0], max(fullDimensions[1], newI.size[1]))
	print 'Minimum crop size:', (minLeftCrop, minTopCrop, minRightCrop, minBottomCrop)
	maxFrameSize = (maxFrameSize[0] - minLeftCrop - minRightCrop, maxFrameSize[1] - minTopCrop - minBottomCrop)
	print 'Max frame size, including cropped area:', maxFrameSize
	targetRatio = float(targetDimension) / float(max(maxFrameSize))
	print 'Target scaling ratio:', targetRatio
	rescaledMaxSize = (int(maxFrameSize[0] * targetRatio), int(maxFrameSize[1] * targetRatio))
	print 'Computing rescaled sizes, and scaling...'
	finalSize = (0, 0)
	resized = []
	normalizedLeftCrops = {}
	normalizedTopCrops = {}
	for f in cropped:
		newSize = (int(round(float(f.size[0]) * targetRatio)), int(round(float(f.size[1]) * targetRatio)))
		resImg = f.resize(newSize, Image.ANTIALIAS)
		resized.append(resImg)
		normalizedLeftCrops[resImg] = int(round(float(crops[f][0] - minLeftCrop) * targetRatio))
		normalizedTopCrops[resImg] = int(round(float(crops[f][1] - minTopCrop) * targetRatio))
		finalSize = (finalSize[0] + newSize[0] + 1, max(finalSize[1], newSize[1] + normalizedTopCrops[resImg]))
	finalSize = (finalSize[0] - 1, finalSize[1])
	print 'Rescaling done, building final image.'
	fullImg = Image.new('RGBA', finalSize, (255, ) * 4)
	currentOffset = 0
	offsetMap = []
	currentOffsetIntervaled = 0
	for f in resized:
		fullImg.paste(f, (currentOffsetIntervaled, normalizedTopCrops[f]), f)
		offsetMap += [currentOffset, f.size[1], normalizedLeftCrops[f]]
		currentOffset += f.size[0]
		currentOffsetIntervaled += f.size[0] + 1
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
	h.write('''{{#switch: {{{1|}}})
  | url = <nowiki></nowiki>
  | map = \n%d,%d,%d,%d,%s
  | height = %d
  | startframe = 16
}}<noinclude>{{3D viewer}}[[Category:3D model images]]
{{Externally linked}}''' % (currentOffset, rescaledMaxSize[0], finalSize[1], xRotNum*2 + 1, ','.join([str(o) for o in offsetMap]), targetDimension))
	h.close()
	print 'Offset map saved to ' + outpootFile + ' offsetmap.txt'

if __name__=='__main__':
	if len(sys.argv) > 1:
		stitch(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))