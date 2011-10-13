import os, Image, ImageFile, sys
try:
	import psyco
	psyco.full()
except:
	pass

targetDimension = 280
targetSize = 512 * 1024 # 512 KB

def autocrop(img):
	load = img.load()
	minX = None
	minY = img.size[1]
	maxX = 0
	maxY = 0
	for x in xrange(img.size[0]):
		yTransparent = True
		for y in xrange(img.size[1]):
			if load[x, y][3] != 0:
				if minX is None:
					minX = x
				if yTransparent:
					# Then now is first non-transparent pixel on column y
					yTransparent = False
					minY = min(minY, y)
				maxX = max(maxX, x)
				maxY = max(maxY, y)
	cropping = (minX, minY, maxX, maxY)
	return (img.crop(cropping).copy(), cropping)

def stitch(imagesDir, colour, outpootFile, numberOfImages):
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
	for i in xrange(numberOfImages):
		for s in ('down', '', 'up'):
			if colour is None:
				filename = imagesDir + os.sep + str(i) + s + '.png'
			else:
				filename = imagesDir + os.sep + str(i) + s + colour + '.png'
			print 'Processing:', filename
			img = Image.open(filename).convert('RGBA')
			maxFrameSize = (max(maxFrameSize[0], img.size[0]), max(maxFrameSize[1], img.size[1]))
			newI, cropping = autocrop(img)
			cropped.append(newI)
			croppedNames[newI] = filename
			crops[newI] = cropping
			if minLeftCrop is None or cropping[0] < minLeftCrop:
				minLeftCrop = cropping[0]
			if minTopCrop is None or cropping[1] < minTopCrop:
				minTopCrop = cropping[1]
			rightCrop = img.size[0] - cropping[2]
			if minRightCrop is None or rightCrop < minRightCrop:
				minRightCrop = rightCrop
			bottomCrop = img.size[1] - cropping[3]
			if minBottomCrop is None or bottomCrop < minBottomCrop:
				minBottomCrop = bottomCrop
			fullDimensions = (fullDimensions[0] + newI.size[0], max(fullDimensions[1], newI.size[1]))
	print 'Minimum crop size:', (minLeftCrop, minTopCrop, minRightCrop, minBottomCrop)
	maxFrameSize = (maxFrameSize[0] - minLeftCrop - minRightCrop, maxFrameSize[1] - minTopCrop - minBottomCrop)
	print 'Max frame size, including cropped area:', maxFrameSize
	targetRatio = float(targetDimension) / float(max(maxFrameSize))
	print 'Target scaling ratio:', targetRatio
	rescaledMaxSize = (int(round(float(maxFrameSize[0]) * targetRatio)), int(round(float(maxFrameSize[1]) * targetRatio)))
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
		offsetMap.append(str(currentOffset))
		offsetMap.append(str(f.size[1]))
		offsetMap.append(str(normalizedLeftCrops[f]))
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
	h.write("""{{#switch: {{{1|}}}
  | url = <nowiki></nowiki>
  | map = \n""" + str(currentOffset) + ',' + str(rescaledMaxSize[0]) + ',' + str(finalSize[1]) + ',3,' + ','.join(offsetMap) + """\n  | width = """ + str(targetDimension) + """
  | height = """ + str(targetDimension) + """
  | startframe = 16
}}<noinclude>{{3D viewer}}[[Category:3D model images]]
{{Externally linked}}""")
	h.close()
	print 'Offset map saved to ' + outpootFile + ' offsetmap.txt'

if __name__=='__main__':
	if len(sys.argv) > 1:
		stitch(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))