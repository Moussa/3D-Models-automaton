import Image
import threading
cimport cython
import numpy as np
cimport numpy as np

cdef inline int getAlphaFor(int wR, int wG, int wB, int bR, int bG, int bB):
	return 255 - (299 * (wR - bR) + 587 * (wG - bG) + 114 * (wB - bB)) / 1000

cdef class pie:
	imageDtype = np.dtype('i')
	exportDtype = np.dtype('uint8')
	cdef public pil
	cdef public numpy
	cdef public int sizeX
	cdef public int sizeY
	cdef public dirty
	def __init__(self, pilImage=None, numpyImage=None, size=None, newColor=None):
		if pilImage is not None:
			self.pil = pilImage.convert('RGBA')
			self.numpy = np.array(self.pil, dtype=pie.imageDtype)
		elif numpyImage is not None:
			self.numpy = numpyImage
			self.pil = Image.fromarray(self.numpy.view(pie.exportDtype)[::,::,::4])
		elif size is not None:
			self.numpy = np.empty((size[0], size[1], 4), dtype=pie.imageDtype)
			if newColor is None:
				newColor = (255, 255, 255, 255)
			self.pil = Image.fromarray(self.numpy.view(pie.exportDtype)[::,::,::4])
		self.sizeX = self.pil.size[0]
		self.sizeY = self.pil.size[1]
		self.dirty = False
	def sync(self):
		if self.dirty:
			self.pil = Image.fromarray(self.numpy.view(pie.exportDtype)[::,::,::4])
			self.dirty = False
	@cython.boundscheck(False)
	@cython.wraparound(False)
	def blackWhiteBlend(self, whiteImage):
		self.dirty = True
		cdef np.ndarray[int, ndim=3] img1 = self.numpy
		cdef np.ndarray[int, ndim=3] img2 = whiteImage.numpy
		cdef np.ndarray[int, ndim=3] blended = (img1 + img2) / 2
		cdef int x, y
		for x in xrange(self.sizeX):
			for y in xrange(self.sizeY):
				blended[y, x, 3] = getAlphaFor(img2[y, x, 0], img2[y, x, 1], img2[y, x, 2], img1[y, x, 0], img1[y, x, 1], img1[y, x, 2])
		return pie(numpyImage=blended)
	def asyncSave(self, *args, **kwargs):
		threading.Thread(target=self.save, args = args, kwargs = kwargs).start()
	def save(self, *args, **kwargs):
		self.sync()
		self.pil.save(*args, **kwargs)

def open(filename):
	return pie(pilImage=Image.open(filename))
