import os
from PIL import Image
from PIL import ImageFile
import numpy
from threading import Thread, Lock
try:
	import psyco
	psyco.full()
except:
	pass

class imageProcessor:
	def __init__(self, suffix=None):
		self.targetDimension = 280
		self.targetSize = 512 * 1024 # 512 KB
		self.maxFrameSize = [0, 0]
		self.finalSize = (0, 0)
		self.minCrop = [999999, 999999, 999999, 999999]
		self.cropped = []
		self.suffix = suffix
		self.lock = Lock()
		self.n = 0

	# Almost never relevant, since the HLMV opening process is so much slower. But it is important for merge.py
	def getNumber(self):
		self.lock.acquire()
		self.cropped.append(None)
		value = self.n
		self.n += 1
		self.lock.release()
		return value
	
	def getBrightness(self, p):
		return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

	# Blends the white image and the black image into an alpha image.
	def blend(self, blackImg, whiteImg, name=None):
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
					255 - int(self.getBrightness(whitePixel) - self.getBrightness(blackPixel))
				)
		if name:
			blackImg.save(name, 'PNG')
		self.cropTask(self.getNumber(), blackImg)

	# Finds the closest-cropped lines that are all white.
	def cropTask(self, n, img):
		alpha = numpy.array(img, dtype=numpy.dtype('i'))[:,:,3]
		horizontal = alpha.any(axis=0).nonzero()[0]
		vertical = alpha.any(axis=1).nonzero()[0]
		cropping = (horizontal[0], vertical[0], horizontal[-1], vertical[-1])
		size = img.size[:]
		newI = img.crop(cropping)
		if size[0] > self.maxFrameSize[0]:
			self.maxFrameSize[0] = size[0]
		if size[1] > self.maxFrameSize[1]:
			self.maxFrameSize[1] = size[1]
		self.cropped[n] = (newI, cropping)
		self.finalSize = (
			self.finalSize[0] + newI.size[0],
			max(self.finalSize[1], newI.size[1] + cropping[1])
		)
		if cropping[0] < self.minCrop[0]:
			self.minCrop[0] = cropping[0]
		if cropping[1] < self.minCrop[1]:
			self.minCrop[1] = cropping[1]
		if size[0] - cropping[2] < self.minCrop[2]:
			self.minCrop[2] = size[0] - cropping[2]
		if size[1] - cropping[3] < self.minCrop[3]:
			self.minCrop[3] = size[1] - cropping[3]

	# Only needs to be called if blend() isn't being called, since blend now calls cropTask.
	def cropImages(self, imagesDir, outpootFile, yRotNum, xRotNum=1):
		threads = []
		for i in range(yRotNum):
			for s in range(xRotNum, -xRotNum-1, -1):
				if self.suffix:
					img = Image.open('%s\%d_%d_%s.png' % (imagesDir, i, s, self.suffix)).convert('RGBA')
				else:
					img = Image.open('%s\%d_%d.png' % (imagesDir, i, s)).convert('RGBA')
				thread = Thread(target=self.cropTask, kwargs={
					'n': self.getNumber(),
					'img': img
				})
				thread.start()
				threads.append(thread)
		for thread in threads:
			thread.join()
		self.stitch(outpootFile, n, xRotNum)

	def stitch(self, outpootFile, n, xRotNum):
		print 'Minimum crop size:', self.minCrop
		self.maxFrameSize = (
			self.maxFrameSize[0] - self.minCrop[0] - self.minCrop[2],
			self.maxFrameSize[1] - self.minCrop[1] - self.minCrop[3]
		)
		print 'Max frame size, including cropped area:', self.maxFrameSize
		targetRatio = float(self.targetDimension) / float(max(self.maxFrameSize))
		print 'Target scaling ratio:', targetRatio
		print 'Computing rescaled sizes, and scaling...'
		self.finalSize = (
			int(self.finalSize[0]*targetRatio + (n-1)), # This is the width, the sum of all the image widths. n-1 because 1 pixel gap between images.
			int((self.finalSize[1] - self.minCrop[1])*targetRatio) # This is the height, which is the max of every image, scaled.
		)
		fullImg = Image.new('RGBA', self.finalSize, (255, ) * 4)
		currentOffset = 0
		offsetMap = []
		currentOffsetIntervaled = 0
		print 'Building final image.'
		for img, cropping in self.cropped:
			newSize = (int(img.size[0] * targetRatio), int(img.size[1] * targetRatio))
			resImg = img.resize(newSize, Image.ANTIALIAS)
			normalizedLeftCrop = int((cropping[0] - self.minCrop[0]) * targetRatio)
			normalizedTopCrop = int((cropping[1] - self.minCrop[1]) * targetRatio)
			fullImg.paste(resImg, (currentOffsetIntervaled, normalizedTopCrop), resImg)
			offsetMap += [currentOffset, resImg.size[1], normalizedLeftCrop]
			currentOffset += resImg.size[0]
			currentOffsetIntervaled += resImg.size[0] + 1
		# Saving
		print 'Done, saving final image to', outpootFile
		if os.path.exists(outpootFile):
			os.remove(outpootFile)
		ImageFile.MAXBLOCK = self.finalSize[0] * self.finalSize[1] * 8 # Make sure there is enough allocated space to save the image as progressive
		quality = 101
		while not os.path.exists(outpootFile) or os.stat(outpootFile).st_size > self.targetSize:
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
{{Externally linked}}''' % (currentOffset, int(self.maxFrameSize[0]*targetRatio), self.finalSize[1], xRotNum*2 + 1, ','.join([str(o) for o in offsetMap]), self.targetDimension))
		h.close()
		print 'Offset map saved to ' + outpootFile + ' offsetmap.txt'
		