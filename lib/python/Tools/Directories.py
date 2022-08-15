# -*- coding: utf-8 -*-
import errno
from inspect import stack
import os
from os import F_OK, R_OK, W_OK, access, chmod, listdir, makedirs, mkdir, readlink, rename, rmdir, sep, stat, statvfs, symlink, utime, walk
from os.path import basename, dirname, exists, getsize, isdir, isfile, islink, join as pathjoin, normpath, splitext
from enigma import eEnv, getDesktop, eGetEnigmaDebugLvl
from errno import ENOENT, EXDEV
from re import compile
from stat import S_IMODE
from unicodedata import normalize
from xml.etree.ElementTree import Element, ParseError, fromstring, parse

DEFAULT_MODULE_NAME = __name__.split(".")[-1]

forceDebug = eGetEnigmaDebugLvl() > 4

pathExists = exists
isMount = os.path.ismount  # Only used in OpenATV /lib/python/Plugins/SystemPlugins/NFIFlash/downloader.py.

SCOPE_HOME = 0  # DEBUG: Not currently used in Enigma2.
SCOPE_TRANSPONDERDATA = 1
SCOPE_SYSETC = 2
SCOPE_FONTS = 3
SCOPE_CONFIG = 4
SCOPE_LANGUAGE = 5
SCOPE_HDD = 6
SCOPE_PLUGINS = 7
SCOPE_PLUGIN = 8
SCOPE_MEDIA = 9
SCOPE_SKINS = 10
SCOPE_GUISKIN = 11
SCOPE_PLAYLIST = 12
SCOPE_CURRENT_PLUGIN_ABSOLUTE = 13
SCOPE_CURRENT_PLUGIN_RELATIVE = 14
SCOPE_KEYMAPS = 15
SCOPE_METADIR = 16
SCOPE_TIMESHIFT = 17
SCOPE_LCDSKIN = 18
SCOPE_AUTORECORD = 19
SCOPE_DEFAULTDIR = 20
SCOPE_DEFAULTPARTITION = 21
SCOPE_DEFAULTPARTITIONMOUNTDIR = 22
SCOPE_LIBDIR = 23

# Deprecated scopes:
SCOPE_ACTIVE_LCDSKIN = SCOPE_LCDSKIN
SCOPE_ACTIVE_SKIN = SCOPE_GUISKIN
SCOPE_CURRENT_LCDSKIN = SCOPE_LCDSKIN
SCOPE_CURRENT_PLUGIN = SCOPE_PLUGIN
SCOPE_CURRENT_SKIN = SCOPE_GUISKIN
SCOPE_SKIN = SCOPE_SKINS
SCOPE_SKIN_IMAGE = SCOPE_SKINS
SCOPE_USERETC = SCOPE_HOME
SCOPE_PLUGIN_ABSOLUTE = SCOPE_CURRENT_PLUGIN_ABSOLUTE
SCOPE_PLUGIN_RELATIVE = SCOPE_CURRENT_PLUGIN_RELATIVE

PATH_CREATE = 0
PATH_DONTCREATE = 1

defaultPaths = {
	SCOPE_HOME: ("", PATH_DONTCREATE),  # User home directory
	SCOPE_TRANSPONDERDATA: (eEnv.resolve("${sysconfdir}/"), PATH_DONTCREATE),
	SCOPE_SYSETC: (eEnv.resolve("${sysconfdir}/"), PATH_DONTCREATE),
	SCOPE_FONTS: (eEnv.resolve("${datadir}/fonts/"), PATH_DONTCREATE),
	SCOPE_CONFIG: (eEnv.resolve("${sysconfdir}/enigma2/"), PATH_CREATE),
	SCOPE_LANGUAGE: (eEnv.resolve("${datadir}/enigma2/po/"), PATH_DONTCREATE),
	SCOPE_HDD: ("/media/hdd/movie/", PATH_DONTCREATE),
	SCOPE_PLUGINS: (eEnv.resolve("${libdir}/enigma2/python/Plugins/"), PATH_CREATE),
	SCOPE_PLUGIN: (eEnv.resolve("${libdir}/enigma2/python/Plugins/"), PATH_CREATE),
	SCOPE_MEDIA: ("/media/", PATH_DONTCREATE),
	SCOPE_SKINS: (eEnv.resolve("${datadir}/enigma2/"), PATH_DONTCREATE),
	SCOPE_GUISKIN: (eEnv.resolve("${datadir}/enigma2/"), PATH_DONTCREATE),
	SCOPE_PLAYLIST: (eEnv.resolve("${sysconfdir}/enigma2/playlist/"), PATH_CREATE),
	SCOPE_CURRENT_PLUGIN_ABSOLUTE: (eEnv.resolve("${libdir}/enigma2/python/Plugins/"), PATH_DONTCREATE),
	SCOPE_CURRENT_PLUGIN_RELATIVE: (eEnv.resolve("${libdir}/enigma2/python/Plugins/"), PATH_DONTCREATE),
	SCOPE_KEYMAPS: (eEnv.resolve("${datadir}/keymaps/"), PATH_CREATE),
	SCOPE_METADIR: (eEnv.resolve("${datadir}/meta"), PATH_CREATE),
	SCOPE_TIMESHIFT: ("/media/hdd/timeshift/", PATH_DONTCREATE),
	SCOPE_LCDSKIN: (eEnv.resolve("${datadir}/enigma2/display/"), PATH_DONTCREATE),
	SCOPE_AUTORECORD: ("/media/hdd/movie/", PATH_DONTCREATE),
	SCOPE_DEFAULTDIR: (eEnv.resolve("${datadir}/enigma2/defaults/"), PATH_CREATE),
	SCOPE_DEFAULTPARTITION: ("/dev/mtdblock6", PATH_DONTCREATE),
	SCOPE_DEFAULTPARTITIONMOUNTDIR: (eEnv.resolve("${datadir}/enigma2/dealer"), PATH_CREATE),
	SCOPE_LIBDIR: (eEnv.resolve("${libdir}/"), PATH_DONTCREATE)
}

scopeConfig = defaultPaths[SCOPE_CONFIG][0]
scopeGUISkin = defaultPaths[SCOPE_GUISKIN][0]
scopeLCDSkin = defaultPaths[SCOPE_LCDSKIN][0]
scopeFonts = defaultPaths[SCOPE_FONTS][0]
scopePlugins = defaultPaths[SCOPE_PLUGINS][0]


def addInList(*paths):
	return [path for path in paths if os.path.isdir(path)]


skinResolveList = []
lcdskinResolveList = []
fontsResolveList = []


def resolveFilename(scope, base="", path_prefix=None):
	# You can only use the ~/ if we have a prefix directory.
	if base.startswith("~/"):
		assert path_prefix is not None  # Assert only works in debug mode!
		if path_prefix:
			base = pathjoin(path_prefix, base[2:])
		else:
			print("[Directories] Warning: resolveFilename called with base starting with '~/' but 'path_prefix' is None!")
	# Don't further resolve absolute paths.
	if base.startswith("/"):
		return normpath(base)
	# If an invalid scope is specified log an error and return None.
	if scope not in defaultPaths:
		print("[Directories] Error: Invalid scope=%d provided to resolveFilename!" % scope)
		return None
	# Ensure that the defaultPaths directories that should exist do exist.
	path, flag = defaultPaths.get(scope)
	if flag == PATH_CREATE and not pathExists(path):
		try:
			makedirs(path)
		except (IOError, OSError) as err:
			print("[Directories] Error %d: Couldn't create directory '%s' (%s)" % (err.errno, path, err.strerror))
			return None
	# Remove any suffix data and restore it at the end.
	suffix = None
	data = base.split(":", 1)
	if len(data) > 1:
		base = data[0]
		suffix = data[1]
	path = base

	def itemExists(resolveList, base):
		baseList = [base]
		if base.endswith(".png"):
			baseList.append("%s%s" % (base[:-3], "svg"))
		elif base.endswith(".svg"):
			baseList.append("%s%s" % (base[:-3], "png"))
		for item in resolveList:
			for base in baseList:
				file = pathjoin(item, base)
				if pathExists(file):
					return file

	# If base is "" then set path to the scope.  Otherwise use the scope to resolve the base filename.
	if base == "":
		path, flags = defaultPaths.get(scope)
		# If the scope is SCOPE_CURRENT_SKIN or SCOPE_ACTIVE_SKIN append the current skin to the scope path.
		if scope in (SCOPE_CURRENT_SKIN, SCOPE_ACTIVE_SKIN):
			# This import must be here as this module finds the config file as part of the config initialisation.
			from Components.config import config
			skin = dirname(config.skin.primary_skin.value)
			path = pathjoin(path, skin)
		elif scope in (SCOPE_CURRENT_PLUGIN_ABSOLUTE, SCOPE_CURRENT_PLUGIN_RELATIVE):
			callingCode = normpath(stack()[1][1])
			plugins = normpath(defaultPaths[SCOPE_PLUGINS][0])
			path = None
			if comparePath(plugins, callingCode):
				pluginCode = callingCode[len(plugins) + 1:].split(sep)
				if len(pluginCode) > 2:
					relative = "%s%s%s" % (pluginCode[0], sep, pluginCode[1])
					path = pathjoin(plugins, relative)
	elif scope in (SCOPE_CURRENT_SKIN, SCOPE_ACTIVE_SKIN):
		global skinResolveList
		if not skinResolveList:
			# This import must be here as this module finds the config file as part of the config initialisation.
			from Components.config import config
			skin = os.path.dirname(config.skin.primary_skin.value)
			skinResolveList = addInList(
					os.path.join(defaultPaths[SCOPE_CONFIG][0], skin),
					os.path.join(defaultPaths[SCOPE_CONFIG][0], "skin_common"),
					defaultPaths[SCOPE_CONFIG][0],
					os.path.join(defaultPaths[SCOPE_SKIN][0], skin),
					os.path.join(defaultPaths[SCOPE_SKIN][0], "skin_default"),
					defaultPaths[SCOPE_SKIN][0]
				)
		file = itemExists(skinResolveList, base)
		if file:
			path = file
	elif scope == SCOPE_CURRENT_LCDSKIN:
		global lcdskinResolveList
		if not lcdskinResolveList:
			# This import must be here as this module finds the config file as part of the config initialisation.
			from Components.config import config
			if hasattr(config.skin, "display_skin"):
				skin = os.path.dirname(config.skin.display_skin.value)
			else:
				skin = ""
			lcdskinResolveList = addInList(
					os.path.join(defaultPaths[SCOPE_CONFIG][0], "display", skin),
					os.path.join(defaultPaths[SCOPE_CONFIG][0], "display", "skin_common"),
					defaultPaths[SCOPE_CONFIG][0],
					os.path.join(defaultPaths[SCOPE_LCDSKIN][0], skin),
					os.path.join(defaultPaths[SCOPE_LCDSKIN][0], "skin_default"),
					defaultPaths[SCOPE_LCDSKIN][0]
				)
		file = itemExists(lcdskinResolveList, base)
		if file:
			path = file
	elif scope == SCOPE_FONTS:
		global fontsResolveList
		if not fontsResolveList:
			# This import must be here as this module finds the config file as part of the config initialisation.
			from Components.config import config
			skin = os.path.dirname(config.skin.primary_skin.value)
			display = os.path.dirname(config.skin.display_skin.value) if hasattr(config.skin, "display_skin") else None
			fontsResolveList = addInList(
					os.path.join(defaultPaths[SCOPE_CONFIG][0], "fonts"),
					os.path.join(defaultPaths[SCOPE_CONFIG][0], skin, "fonts"),
					os.path.join(defaultPaths[SCOPE_CONFIG][0], skin)
				)
			if display:
				fontsResolveList += addInList(os.path.join(defaultPaths[SCOPE_CONFIG][0], "display", display))
			fontsResolveList += addInList(
					os.path.join(defaultPaths[SCOPE_CONFIG][0], "skin_common"),
					defaultPaths[SCOPE_CONFIG][0],
					os.path.join(defaultPaths[SCOPE_SKIN][0], skin, "fonts"),
					os.path.join(defaultPaths[SCOPE_SKIN][0], skin),
					os.path.join(defaultPaths[SCOPE_SKIN][0], "skin_default", "fonts"),
					os.path.join(defaultPaths[SCOPE_SKIN][0], "skin_default")
				)
			if display:
				fontsResolveList += addInList(os.path.join(defaultPaths[SCOPE_LCDSKIN][0], display))
			fontsResolveList += addInList(
					os.path.join(defaultPaths[SCOPE_LCDSKIN][0], "skin_default"),
					defaultPaths[SCOPE_FONTS][0]
				)
		for item in fontsResolveList:
			file = pathjoin(item, base)
			if pathExists(file):
				path = file
				break
	elif scope == SCOPE_CURRENT_PLUGIN:
		file = pathjoin(defaultPaths[SCOPE_PLUGINS][0], base)
		if pathExists(file):
			path = file
	elif scope in (SCOPE_CURRENT_PLUGIN_ABSOLUTE, SCOPE_CURRENT_PLUGIN_RELATIVE):
		callingCode = normpath(stack()[1][1])
		plugins = normpath(defaultPaths[SCOPE_PLUGINS][0])
		path = None
		if comparePath(plugins, callingCode):
			pluginCode = callingCode[len(plugins) + 1:].split(sep)
			if len(pluginCode) > 2:
				relative = pathjoin("%s%s%s" % (pluginCode[0], sep, pluginCode[1]), base)
				path = pathjoin(plugins, relative)
	else:
		path, flags = defaultPaths.get(scope)
		path = pathjoin(path, base)
	path = normpath(path)
	# If the path is a directory then ensure that it ends with a "/".
	if isdir(path) and not path.endswith("/"):
		path += "/"
	if scope == SCOPE_CURRENT_PLUGIN_RELATIVE:
		path = path[len(plugins) + 1:]
	# If a suffix was supplier restore it.
	if suffix is not None:
		path = "%s:%s" % (path, suffix)
	return path


def comparePath(leftPath, rightPath):
	if leftPath.endswith(sep):
		leftPath = leftPath[:-1]
	if rightPath.endswith(sep):
		rightPath = rightPath[:-1]
	left = leftPath.split(sep)
	right = rightPath.split(sep)
	for segment in range(len(left)):
		if left[segment] != right[segment]:
			return False
	return True


def bestRecordingLocation(candidates):
	path = ""
	biggest = 0
	for candidate in candidates:
		try:
			# Must have some free space (i.e. not read-only).
			stat = statvfs(candidate[1])
			if stat.f_bavail:
				# Free space counts double.
				size = (stat.f_blocks + stat.f_bavail) * stat.f_bsize
				if size > biggest:
					biggest = size
					path = candidate[1]
		except (IOError, OSError) as err:
			print("[Directories] Error %d: Couldn't get free space for '%s' (%s)" % (err.errno, candidate[1], err.strerror))
	return path


def defaultRecordingLocation(candidate=None):
	if candidate and pathExists(candidate):
		return candidate
	# First, try whatever /hdd points to, or /media/hdd.
	try:
		path = readlink("/hdd")
	except OSError:
		path = "/media/hdd"
	if not pathExists(path):
		# Find the largest local disk.
		from Components import Harddisk
		mounts = [m for m in Harddisk.getProcMounts() if m[1].startswith("/media/")]
		# Search local devices first, use the larger one
		path = bestRecordingLocation([m for m in mounts if m[0].startswith("/dev/")])
		# If we haven't found a viable candidate yet, try remote mounts.
		if not path:
			path = bestRecordingLocation([m for m in mounts if not m[0].startswith("/dev/")])
	if path:
		# If there's a movie subdir, we'd probably want to use that.
		movie = pathjoin(path, "movie")
		if isdir(movie):
			path = movie
		if not path.endswith("/"):
			path += "/"  # Bad habits die hard, old code relies on this.
	return path


def createDir(path, makeParents=False):
	try:
		if makeParents:
			makedirs(path)
		else:
			mkdir(path)
		return 1
	except OSError:
		return 0


def removeDir(path):
	try:
		rmdir(path)
		return 1
	except OSError:
		return 0


def fileExists(f, mode="r"):
	if mode == "r":
		acc_mode = R_OK
	elif mode == "w":
		acc_mode = W_OK
	else:
		acc_mode = F_OK
	return access(f, acc_mode)

def fileAccess(file, mode="r"):
	accMode = F_OK
	if "r" in mode:
		accMode |= R_OK
	if "w" in mode:
		accMode |= W_OK
	result = False
	try:
		result = access(file, accMode)
	except (IOError, OSError) as err:
		print("[Directories] Error %d: Couldn't determine file '%s' access mode! (%s)" % (err.errno, file, err.strerror))
	return result

def fileCheck(f, mode="r"):
	return fileExists(f, mode) and f

def fileExists(file, mode="r"):
	return fileAccess(file, mode) and file

def fileContains(file, content, mode="r"):
	result = False
	if fileExists(file, mode):
		fd = open(file, mode)
		text = fd.read()
		fd.close()
		if content in text:
			result = True
	return result

def fileHas(f, content, mode="r"):
	result = False
	if fileExists(f, mode):
		file = open(f, mode)
		text = file.read()
		file.close()
		if content in text:
			result = True
	return result


def fileReadLine(filename, default=None, source=DEFAULT_MODULE_NAME, debug=False):
	line = None
	try:
		with open(filename, "r") as fd:
			line = fd.read().strip()
		msg = "Read"
	except (IOError, OSError) as err:
		if err.errno != ENOENT:  # ENOENT - No such file or directory.
			print("[%s] Error %d: Unable to read a line from file '%s'! (%s)" % (source, err.errno, filename, err.strerror))
		line = default
		msg = "Default"
	if debug or forceDebug:
		print("[%s] Line %d: %s '%s' from file '%s'." % (source, stack()[1][0].f_lineno, msg, line, filename))
	return line


def fileWriteLine(filename, line, source=DEFAULT_MODULE_NAME, debug=False):
	try:
		with open(filename, "w") as fd:
			fd.write(str(line))
		msg = "Wrote"
		result = 1
	except (IOError, OSError) as err:
		print("[%s] Error %d: Unable to write a line to file '%s'! (%s)" % (source, err.errno, filename, err.strerror))
		msg = "Failed to write"
		result = 0
	if debug or forceDebug:
		print("[%s] Line %d: %s '%s' to file '%s'." % (source, stack()[1][0].f_lineno, msg, line, filename))
	return result


def fileReadLines(filename, default=None, source=DEFAULT_MODULE_NAME, debug=False):
	lines = None
	try:
		with open(filename, "r") as fd:
			lines = fd.read().splitlines()
		msg = "Read"
	except (IOError, OSError) as err:
		if err.errno != ENOENT:  # ENOENT - No such file or directory.
			print("[%s] Error %d: Unable to read lines from file '%s'! (%s)" % (source, err.errno, filename, err.strerror))
		lines = default
		msg = "Default"
	if debug or forceDebug:
		length = len(lines) if lines else 0
		print("[%s] Line %d: %s %d lines from file '%s'." % (source, stack()[1][0].f_lineno, msg, length, filename))
	return lines


def fileWriteLines(filename, lines, source=DEFAULT_MODULE_NAME, debug=False):
	try:
		with open(filename, "w") as fd:
			if isinstance(lines, list):
				lines.append("")
				lines = "\n".join(lines)
			fd.write(lines)
		msg = "Wrote"
		result = 1
	except (IOError, OSError) as err:
		print("[%s] Error %d: Unable to write %d lines to file '%s'! (%s)" % (source, err.errno, len(lines), filename, err.strerror))
		msg = "Failed to write"
		result = 0
	if debug or forceDebug:
		print("[%s] Line %d: %s %d lines to file '%s'." % (source, stack()[1][0].f_lineno, msg, len(lines), filename))
	return result


def fileReadXML(filename, default=None, source=DEFAULT_MODULE_NAME, debug=False):
	dom = None
	try:
		with open(filename, "r") as fd:  # This open gets around a possible file handle leak in Python's XML parser.
			try:
				dom = parse(fd).getroot()
				msg = "Read"
			except ParseError as err:
				fd.seek(0)
				content = fd.readlines()
				line, column = err.position
				print("[%s] XML Parse Error: '%s' in '%s'!" % (source, err, filename))
				data = content[line - 1].replace("\t", " ").rstrip()
				print("[%s] XML Parse Error: '%s'" % (source, data))
				print("[%s] XML Parse Error: '%s^%s'" % (source, "-" * column, " " * (len(data) - column - 1)))
			except Exception as err:
				print("[%s] Error: Unable to parse data in '%s' - '%s'!" % (source, filename, err))
	except (IOError, OSError) as err:
		if err.errno == ENOENT:  # ENOENT - No such file or directory.
			print("[%s] Warning: File '%s' does not exist!" % (source, filename))
		else:
			print("[%s] Error %d: Opening file '%s'!  (%s)" % (source, err.errno, filename, err.strerror))
	except Exception as err:
		print("[%s] Error: Unexpected error opening/parsing file '%s'!  (%s)" % (source, filename, err))
		print_exc()
	if dom is None:
		if default and isinstance(default, str):
			dom = fromstring(default)
			msg = "Default (XML)"
		elif default and isinstance(default, type(Element(None))):  # This handles a bug in Python 2 where the Element object is *not* a class type in cElementTree!!!
			dom = default
			msg = "Default (DOM)"
		else:
			msg = "Failed to read"
	if debug or forceDebug:
		print("[%s] Line %d: %s from XML file '%s'." % (source, stack()[1][0].f_lineno, msg, filename))
	return dom


def getRecordingFilename(basename, dirname=None):
	# Filter out non-allowed characters.
	non_allowed_characters = "/.\\:*?<>|\""
	basename = basename.replace("\x86", "").replace("\x87", "")
	filename = ""
	for c in basename:
		if c in non_allowed_characters or ord(c) < 32:
			c = "_"
		filename += c
	# Max filename length for ext4 is 255 (minus 8 characters for .ts.meta)
	# but must not truncate in the middle of a multi-byte utf8 character!
	# So convert the truncation to unicode and back, ignoring errors, the
	# result will be valid utf8 and so xml parsing will be OK.
	filename = filename[:247]
	if dirname is not None:
		if not dirname.startswith("/"):
			dirname = os.path.join(defaultRecordingLocation(), dirname)
	else:
		dirname = defaultRecordingLocation()
	filename = os.path.join(dirname, filename)
	path = filename
	i = 1
	while True:
		if not os.path.isfile(path + ".ts"):
			return path
		path += "_%03d" % i
		i += 1

# This is clearly a hack:
#


def InitFallbackFiles():
	resolveFilename(SCOPE_CONFIG, "userbouquet.favourites.tv")
	resolveFilename(SCOPE_CONFIG, "bouquets.tv")
	resolveFilename(SCOPE_CONFIG, "userbouquet.favourites.radio")
	resolveFilename(SCOPE_CONFIG, "bouquets.radio")

# Returns a list of tuples containing pathname and filename matching the given pattern
# Example-pattern: match all txt-files: ".*\.txt$"
#


def crawlDirectory(directory, pattern):
	list = []
	if directory:
		expression = compile(pattern)
		for root, dirs, files in walk(directory):
			for file in files:
				if expression.match(file) is not None:
					list.append((root, file))
	return list


def copyfile(src, dst):
	f1 = None
	f2 = None
	status = 0
	try:
		f1 = open(src, "rb")
		if isdir(dst):
			dst = pathjoin(dst, basename(src))
		f2 = open(dst, "w+b")
		while True:
			buf = f1.read(16 * 1024)
			if not buf:
				break
			f2.write(buf)
	except (IOError, OSError) as err:
		print("[Directories] Error %d: Copying file '%s' to '%s'! (%s)" % (err.errno, src, dst, err.strerror))
		status = -1
	if f1 is not None:
		f1.close()
	if f2 is not None:
		f2.close()
	try:
		st = stat(src)
		try:
			chmod(dst, S_IMODE(st.st_mode))
		except (IOError, OSError) as err:
			print("[Directories] Error %d: Setting modes from '%s' to '%s'! (%s)" % (err.errno, src, dst, err.strerror))
		try:
			utime(dst, (st.st_atime, st.st_mtime))
		except (IOError, OSError) as err:
			print("[Directories] Error %d: Setting times from '%s' to '%s'! (%s)" % (err.errno, src, dst, err.strerror))
	except (IOError, OSError) as err:
		print("[Directories] Error %d: Obtaining stats from '%s' to '%s'! (%s)" % (err.errno, src, dst, err.strerror))
	return status


def copytree(src, dst, symlinks=False):
	names = listdir(src)
	if isdir(dst):
		dst = pathjoin(dst, basename(src))
		if not isdir(dst):
			mkdir(dst)
	else:
		makedirs(dst)
	for name in names:
		srcname = pathjoin(src, name)
		dstname = pathjoin(dst, name)
		try:
			if symlinks and islink(srcname):
				linkto = readlink(srcname)
				symlink(linkto, dstname)
			elif isdir(srcname):
				copytree(srcname, dstname, symlinks)
			else:
				copyfile(srcname, dstname)
		except (IOError, OSError) as err:
			print("[Directories] Error %d: Copying tree '%s' to '%s'! (%s)" % (err.errno, srcname, dstname, err.strerror))
	try:
		st = stat(src)
		try:
			chmod(dst, S_IMODE(st.st_mode))
		except (IOError, OSError) as err:
			print("[Directories] Error %d: Setting modes from '%s' to '%s'! (%s)" % (err.errno, src, dst, err.strerror))
		try:
			utime(dst, (st.st_atime, st.st_mtime))
		except (IOError, OSError) as err:
			print("[Directories] Error %d: Setting times from '%s' to '%s'! (%s)" % (err.errno, src, dst, err.strerror))
	except (IOError, OSError) as err:
		print("[Directories] Error %d: Obtaining stats from '%s' to '%s'! (%s)" % (err.errno, src, dst, err.strerror))

# Renames files or if source and destination are on different devices moves them in background
# input list of (source, destination)
#


def moveFiles(fileList):
	errorFlag = False
	movedList = []
	try:
		for item in fileList:
			rename(item[0], item[1])
			movedList.append(item)
	except (IOError, OSError) as err:
		if err.errno == errno.EXDEV:  # Invalid cross-device link
			print("[Directories] Warning: Cannot rename across devices, trying slower move.")
			# from Tools.CopyFiles import moveFiles as extMoveFiles  # OpenViX, OpenATV, Beyonwiz
			from Screens.CopyFiles import moveFiles as extMoveFiles  # OpenPLi
			extMoveFiles(fileList, item[0])
			print("[Directories] Moving files in background.")
		else:
			print("[Directories] Error %d: Moving file '%s' to '%s'! (%s)" % (err.errno, item[0], item[1], err.strerror))
			errorFlag = True
	if errorFlag:
		print("[Directories] Reversing renamed files due to error.")
		for item in movedList:
			try:
				rename(item[1], item[0])
			except (IOError, OSError) as err:
				print("[Directories] Error %d: Renaming '%s' to '%s'! (%s)" % (err.errno, item[1], item[0], err.strerror))
				print("[Directories] Failed to undo move:", item)


def getSize(path, pattern=".*"):
	path_size = 0
	if isdir(path):
		files = crawlDirectory(path, pattern)
		for file in files:
			filepath = pathjoin(file[0], file[1])
			path_size += getsize(filepath)
	elif isfile(path):
		path_size = getsize(path)
	return path_size


def lsof():
	lsof = []
	for pid in listdir("/proc"):
		if pid.isdigit():
			try:
				prog = readlink(pathjoin("/proc", pid, "exe"))
				dir = pathjoin("/proc", pid, "fd")
				for file in [pathjoin(dir, file) for file in listdir(dir)]:
					lsof.append((pid, prog, readlink(file)))
			except OSError:
				pass
	return lsof


def getExtension(file):
	filename, extension = splitext(file)
	return extension


def mediafilesInUse(session):
	from Components.MovieList import KNOWN_EXTENSIONS
	files = [basename(x[2]) for x in lsof() if getExtension(x[2]) in KNOWN_EXTENSIONS]
	service = session.nav.getCurrentlyPlayingServiceOrGroup()
	filename = service and service.getPath()
	if filename:
		if "://" in filename:  # When path is a stream ignore it.
			filename = None
		else:
			filename = basename(filename)
	return set([file for file in files if not(filename and file == filename and files.count(filename) < 2)])

# Prepare filenames for use in external shell processing. Filenames may
# contain spaces or other special characters.  This method adjusts the
# filename to be a safe and single entity for passing to a shell.
#


def shellquote(s):
	return "'%s'" % s.replace("'", "'\\''")

def isPluginInstalled(pluginName, pluginFile="plugin", pluginType=None):
	types = ["Extensions", "SystemPlugins"]
	if pluginType:
		types = [pluginType]
	extensions = ["c", ""]
	for type in types:
		for extension in extensions:
			if isfile(pathjoin(defaultPaths[SCOPE_PLUGINS][0], type, pluginName, "%s.py%s" % (pluginFile, extension))):
				return True
	return False

def sanitizeFilename(filename):
	"""Return a fairly safe version of the filename.
	We don't limit ourselves to ascii, because we want to keep municipality
	names, etc, but we do want to get rid of anything potentially harmful,
	and make sure we do not exceed Windows filename length limits.
	Hence a less safe blacklist, rather than a whitelist.
	"""
	blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0", "(", ")", " "]
	reserved = [
		"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
		"COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
		"LPT6", "LPT7", "LPT8", "LPT9",
	]  # Reserved words on Windows
	filename = "".join(c for c in filename if c not in blacklist)
	# Remove all charcters below code point 32
	filename = "".join(c for c in filename if 31 < ord(c))
	filename = normalize("NFKD", filename)
	filename = filename.rstrip(". ")  # Windows does not allow these at end
	filename = filename.strip()
	if all([x == "." for x in filename]):
		filename = "__" + filename
	if filename in reserved:
		filename = "__" + filename
	if len(filename) == 0:
		filename = "__"
	if len(filename) > 255:
		parts = split(r"/|\\", filename)[-1].split(".")
		if len(parts) > 1:
			ext = "." + parts.pop()
			filename = filename[:-len(ext)]
		else:
			ext = ""
		if filename == "":
			filename = "__"
		if len(ext) > 254:
			ext = ext[254:]
		maxl = 255 - len(ext)
		filename = filename[:maxl]
		filename = filename + ext
		# Re-check last character (if there was no extension)
		filename = filename.rstrip(". ")
		if len(filename) == 0:
			filename = "__"
	return filename
