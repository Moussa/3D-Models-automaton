import os, Image, ImageFile, sys, numpy
try:
	import psyco
	psyco.full()
except:
	pass

from threading import Thread
# This pool should NOT use multiprocessing in order to avoid copying huge image objects around from process to process

targetDimension = 280
targetSize = 512 * 1024 # 512 KB
global maxFrameSize, minCrop, cropped, crops, fullDimensions
maxFrameSize = [0, 0]
minCrop = [sys.maxint, sys.maxint, sys.maxint, sys.maxint]
cropped = []
crops = {}
fullDimensions = (0, 0)
_imageDtype = numpy.dtype('i')

# Finds the closest-cropped lines that are all white.
def cropTask(i, s, filename):
	img = Image.open(filename).convert('RGBA')
	alpha = numpy.array(img, dtype=_imageDtype)[:,:,3]
	horizontal = alpha.any(axis=0).nonzero()[0]
	vertical = alpha.any(axis=1).nonzero()[0]
	cropping = (horizontal[0], vertical[0], horizontal[-1], vertical[-1])
	global maxFrameSize, minCrop, cropped, crops, fullDimensions
	size = img.size[:]
	newI = img.crop(cropping)
	if size[0] > maxFrameSize[0]:
		maxFrameSize[0] = size[0]
	if size[1] > maxFrameSize[1]:
		maxFrameSize[1] = size[1]
	cropped.append(newI)
	crops[newI] = cropping
	if cropping[0] < minCrop[0]:
		minCrop[0] = cropping[0]
	if cropping[1] < minCrop[1]:
		minCrop[1] = cropping[1]
	if size[0] - cropping[2] < minCrop[2]:
		minCrop[2] = size[0] - cropping[2]
	if size[1] - cropping[3] < minCrop[3]:
		minCrop[3] = size[1] - cropping[3]
	fullDimensions = (fullDimensions[0] + newI.size[0], max(fullDimensions[1], newI.size[1]))

def stitch(imagesDir, colour, outpootFile, yRotNum, xRotNum=1):
	outpootFile = imagesDir + os.sep + outpootFile
	print 'Cropping frames...'
	threads = []
	for i in range(yRotNum):
		for s in range(-xRotNum, xRotNum + 1):
			thread = Thread(target=cropTask, kwargs={
				'i': i,
				's': s,
				'filename': '%s\%d_%d.png' % (imagesDir, i, s)
			})
			thread.start()
			threads.append(thread)
	for thread in threads:
		thread.join()
	global maxFrameSize, minCrop, cropped, crops, fullDimensions
	print 'Minimum crop size:', minCrop
	maxFrameSize = (maxFrameSize[0] - minCrop[0] - minCrop[2], maxFrameSize[1] - minCrop[1] - minCrop[3])
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
		newSize = (int(f.size[0] * targetRatio), int(f.size[1] * targetRatio))
		resImg = f.resize(newSize, Image.ANTIALIAS)
		resized.append(resImg)
		normalizedLeftCrops[resImg] = int((crops[f][0] - minCrop[0]) * targetRatio)
		normalizedTopCrops[resImg] = int((crops[f][1] - minCrop[1]) * targetRatio)
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
	h.write('''{{#switch: {{{1|}}}
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