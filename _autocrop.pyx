import Image
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
cdef _autocrop(img):
	cdef int sizeX, sizeY, minX, minY, maxX, maxY, x, y
	cdef bool yTransparent
	sizeX = img.size[0]
	sizeY = img.size[1]
	load = img.load()
	minX = -1
	minY = sizeY
	maxX = 0
	maxY = 0
	for x in xrange(sizeX):
		yTransparent = True
		for y in xrange(sizeY):
			if load[x, y][3] != 0:
				if minX == -1:
					minX = x
				if yTransparent:
					yTransparent = False
					minY = <int>min(minY, y)
				maxX = <int>max(maxX, x)
				maxY = <int>max(maxY, y)
	cropping = (minX, minY, maxX, maxY)
	return (img.crop(cropping), cropping)

def autocrop(img):
	return _autocrop(img)
