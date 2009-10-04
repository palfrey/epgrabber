# Python enumeration metaclass
# Taken from http://www.python.org/doc/essays/metaclasses/Enum.py

"""Enumeration metaclass.

XXX This is very much a work in progress.

"""

import string

class EnumMetaClass:
	"""Metaclass for enumeration.

	To define your own enumeration, do something like

	class Color(Enum):
		red = 1
		green = 2
		blue = 3

	Now, Color.red, Color.green and Color.blue behave totally
	different: they are enumerated values, not integers.

	Enumerations cannot be instantiated; however they can be
	subclassed.

	"""

	def __init__(self, name, bases, dict):
		"""Constructor -- create an enumeration.

		Called at the end of the class statement.  The arguments are
		the name of the new class, a tuple containing the base
		classes, and a dictionary containing everything that was
		entered in the class' namespace during execution of the class
		statement.  In the above example, it would be {'red': 1,
		'green': 2, 'blue': 3}.

		"""
		for base in bases:
			if base.__class__ is not EnumMetaClass:
				raise TypeError, "Enumeration base class must be enumeration"
		bases = filter(lambda x: x is not Enum, bases)
		self.__name__ = name
		self.__bases__ = bases
		self.__dict = {}
		for key, value in dict.items():
			self.__dict[key] = EnumInstance(name, key, value)

	def __getattr__(self, name):
		"""Return an enumeration value.

		For example, Color.red returns the value corresponding to red.

		XXX Perhaps the values should be created in the constructor?

		This looks in the class dictionary and if it is not found
		there asks the base classes.

		The special attribute __members__ returns the list of names
		defined in this class (it does not merge in the names defined
		in base classes).

		"""
		if name == '__members__':
			return [x for x in self.__dict.keys() if len(x)<2 or x[:2]!="__"]

		try:
			return self.__dict[name]
		except KeyError:
			for base in self.__bases__:
				try:
					return getattr(base, name)
				except AttributeError:
					continue

		raise AttributeError, name

	def valid(self,name):
		if name in self.__dict:
			return self.__dict[name]
		else:
			raise ValueError, "Specified name not in enum"

	def getWithValue(self,value):
		try:
			for k in self.__dict:
				if k[0] == "_":
					continue
				if self.__dict[k].value() == value:
					return self.__dict[k]
		except KeyError:
			for base in self.__bases__:
				try:
					return base.getWithValue(value)
				except AttributeError:
					continue

		raise AttributeError, value
	
	def __repr__(self):
		s = self.__name__
		if self.__bases__:
			s = s + '(' + string.join(map(lambda x: x.__name__,
										  self.__bases__), ", ") + ')'
		if self.__dict:
			list = []
			for key, value in self.__dict.items():
				if key[0] == "_":
					continue
				list.append("%s: %s" % (key, value.value()))
			s = "%s: {%s}" % (s, string.join(list, ", "))
		return s
	
	def name(self):
		return self.__name__

	def list(self,separator=", "):
		return separator.join(self.__members__)

	def __iter__(self):
		values = [self.__dict[x] for x in self.__members__ if x[0]!="_"]
		for base in self.__bases__:
			values.extend(list(base.__iter__(self)))
		return iter(sorted(values))

class EnumInstance:
	"""Class to represent an enumeration value.

	EnumInstance('Color', 'red', 12) prints as 'Color.red' and behaves
	like the integer 12 when compared, but doesn't support arithmetic.

	XXX Should it record the actual enumeration rather than just its
	name?

	"""

	def __init__(self, classname, enumname, value):
		self.__classname = classname
		self.__enumname = enumname
		self.__value = value

	def __repr__(self):
		return "EnumInstance(%s, %s, %s)" % (`self.__classname`,
											 `self.__enumname`,
											 `self.__value`)

	def __str__(self):
		return "%s.%s" % (self.__classname, self.__enumname)

	def __cmp__(self, other):
		if other == None:
			return 1
		
		try:
			if isinstance(other,EnumInstance):
				return cmp(self.__value,other.__value)
		except TypeError:
			pass
		return cmp(self.__value, other)
	
	def name(self):
		return self.__enumname

	def value(self):
		return self.__value


# Create the base class for enumerations.
# It is an empty enumeration.
Enum = EnumMetaClass("Enum", (), {})

from optparse import OptionParser,OptionValueError,Option
from copy import copy

def check_enum(option, opt, value):
	try:
		return option.enum.valid(value)
	except ValueError:
		raise OptionValueError,"'%s' is an invalid type for %s (valid types are %s)"%(value,option, ", ".join(option.enum.__members__))

class EnumOption (Option):
	TYPES = Option.TYPES + ("enum",)
	TYPE_CHECKER = copy(Option.TYPE_CHECKER)
	TYPE_CHECKER["enum"] = check_enum
	ATTRS = copy(Option.ATTRS)
	ATTRS.append("enum")

class SpecificParser(OptionParser):
	def __init__(self,*args,**kwargs):
		if kwargs.has_key('option_class'):
			if not issubclass(kwargs['option_class'],self._option):
				raise Exception, "option_class must be a subclass of %s"%self._option.__name__
		else:
			kwargs['option_class'] = self._option
		OptionParser.__init__(self,*args,**kwargs)
	
class EnumOptionParser(SpecificParser):
	_option = EnumOption

	def add_option(self, *args, **kwargs):
		if kwargs.has_key('enum') and not kwargs.has_key('help'):
			kwargs['help'] = "%s ("%kwargs['enum'].name()+"|".join(kwargs['enum'].__members__)+")"
		OptionParser.add_option(self,*args,**kwargs)

def _test():

	class Color(Enum):
		red = 1
		green = 2
		blue = 3

	print Color.red
	print dir(Color)

	print Color.red == Color.red
	print Color.red == Color.blue
	print Color.red == 1
	print Color.red == 2

	class ExtendedColor(Color):
		white = 0
		orange = 4
		yellow = 5
		purple = 6
		black = 7

	print ExtendedColor.orange
	print ExtendedColor.red

	print Color.red == ExtendedColor.red

	class OtherColor(Enum):
		white = 4
		blue = 5

	class MergedColor(Color, OtherColor):
		pass

	print MergedColor.red
	print MergedColor.white

	print Color
	print ExtendedColor
	print OtherColor
	print MergedColor



if __name__ == '__main__':
	_test()
