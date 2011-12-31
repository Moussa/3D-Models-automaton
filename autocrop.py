import Image, numpy
try:
	import psyco
	psyco.full()
except:
	pass

_imageDtype = numpy.dtype('i')
def autocrop(img):
	alpha = numpy.array(img, dtype=_imageDtype)[:,:,3]
	horizontal = alpha.any(axis=0).nonzero()[0]
	vertical = alpha.any(axis=1).nonzero()[0]
	cropping = (horizontal[0], vertical[0], horizontal[-1], vertical[-1])
	return (img.crop(cropping), cropping)
