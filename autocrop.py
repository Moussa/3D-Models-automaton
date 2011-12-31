import Image
try:
	import psyco
	psyco.full()
except:
	pass

def autocrop(img):
	sizeX = img.size[0]
	sizeY = img.size[1]
	load = img.load()
	minX = -1
	minY = sizeY
	maxX = 0
	maxY = 0
	yRange = xrange(sizeY)
	for x in xrange(sizeX):
		yTransparent = 1
		for y in yRange:
			if load[x, y][3] != 0:
				if minX == -1:
					minX = x
				if yTransparent:
					yTransparent = 0
					minY = min(minY, y)
				maxX = max(maxX, x)
				maxY = max(maxY, y)
	cropping = (minX, minY, maxX, maxY)
	return (img.crop(cropping), cropping)
