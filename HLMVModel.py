import _winreg, sys, re

class HLMVModelRegistryKey:
	""" class to wrap the registry entries for HLMV model registry keys
	"""
	def __init__(self, weaponKey):
		""" Initial Parameters:
					weaponkey -> key name for model located at HKEY_CURRENT_USER\Software\Valve\hlmv\
		"""
		try:
			self.itemkey = _winreg.OpenKey(
										   _winreg.HKEY_CURRENT_USER,
										   "Software\\Valve\\hlmv\\" + weaponKey,
										   0,
										   _winreg.KEY_ALL_ACCESS
										   )
		except WindowsError:
			print 'Weapon key \'' + weaponKey + '\' doesn\'t exist. Check spelling.'
			sys.exit(1)

	def returnKeyData(self):
		try:
			dataList = []
			i = 0
			while True:
				name, value, type = _winreg.EnumValue(self.itemkey, i)
				dict = {'name': repr(name), 'value': repr(value), 'type': repr(type)}
				dataList.append(dict)
				i += 1
		except WindowsError:
			pass
		return dataList

	def setKeyValue(self, name, type, value):
		_winreg.SetValueEx(self.itemkey, name, 0, type, value)

	def returnRotation(self):
		value, type = _winreg.QueryValueEx(self.itemkey, 'Rot')
		dataParser = re.compile(r'\(([-+]?[0-9]*\.?[0-9]+) ([-+]?[0-9]*\.?[0-9]+) ([-+]?[0-9]*\.?[0-9]+)\)')
		values = dataParser.search(value)
		return {'x': float(values.group(1)), 'y': float(values.group(2)), 'z': float(values.group(3))}
	
	def returnTranslation(self):
		value, type = _winreg.QueryValueEx(self.itemkey, 'Trans')
		dataParser = re.compile(r'\(([-+]?[0-9]*\.?[0-9]+) ([-+]?[0-9]*\.?[0-9]+) ([-+]?[0-9]*\.?[0-9]+)\)')
		values = dataParser.search(value)
		return {'x': float(values.group(1)), 'y': float(values.group(2)), 'z': float(values.group(3))}

	def setRotation(self, x=None, y=None, z=None):
		if x is None:
			x = self.returnRotation()['x']
		if y is None:
			y = self.returnRotation()['y']
		if z is None:
			z = self.returnRotation()['z']
		value = '(%s %s %s)' % ('%0.6f' % float(x), '%0.6f' % float(y), '%0.6f' % float(z))
		self.setKeyValue('Rot', _winreg.REG_SZ, value)

	def setTranslation(self, x=None, y=None, z=None):
		if x is None:
			x = self.returnTranslation()['x']
		if y is None:
			y = self.returnTranslation()['y']
		if z is None:
			z = self.returnTranslation()['z']
		value = '(%s %s %s)' % ('%0.6f' % float(x), '%0.6f' % float(y), '%0.6f' % float(z))
		self.setKeyValue('Trans', _winreg.REG_SZ, value)
	
	def setBGColour(self, r, g, b, a):
		r = float("%.6f" % (float(r)/255.0))
		g = float("%.6f" % (float(g)/255.0))
		b = float("%.6f" % (float(b)/255.0))
		a = float("%.6f" % (float(a)/255.0))
		value = '(%s %s %s %s)' % (r, g, b, a)
		self.setKeyValue('bgColor', _winreg.REG_SZ, value)
	
	def setNormalMapping(self, value):
		if type(value) is type(True):
			if value:
				self.setKeyValue('enablenormalmapping', _winreg.REG_DWORD, 1)
			else:
				self.setKeyValue('enablenormalmapping', _winreg.REG_DWORD, 0)
		else:
			print 'argument is not a bool'

# Example usage
"""
ambassador = HLMVModelRegistryKey('models.weapons.c_models.c_ambassador.c_ambassador.mdl')
ambassador.setRotation(0.0, 0.0, 0.01)
print 'Rot =', ambassador.returnRotation()
print 'Trans =', ambassador.returnTranslation()
ambassador.setRotation(y=0.01)
print 'Rot =', ambassador.returnRotation()"""