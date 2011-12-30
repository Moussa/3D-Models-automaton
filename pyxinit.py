import pyximport
import numpy as np

_initialized = False

def init():
	global _initialized
	if not _initialized:
		pyximport.install(
			setup_args = {
				'include_dirs': [np.get_include()]
			}
		)
		_initialized = True

init()
