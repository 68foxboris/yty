from array import array
from binascii import hexlify
from fcntl import ioctl
from glob import glob
from locale import format_string
from os import popen, stat
from os.path import isfile
from re import search
from socket import AF_INET, SOCK_DGRAM, inet_ntoa, socket
from struct import pack, unpack
from subprocess import PIPE, Popen
from sys import maxsize, modules, version as pyversion
from time import localtime, strftime

from Tools.HardwareInfo import HardwareInfo
from Tools.Directories import fileReadLine, fileReadLines
MODULE_NAME = __name__.split(".")[-1]


def _ifinfo(sock, addr, ifname):
	iface = pack('256s', bytes(ifname[:15], 'utf-8'))
	info = ioctl(sock.fileno(), addr, iface)
	if addr == 0x8927:
		return ''.join(['%02x:' % ord(chr(char)) for char in info[18:24]])[:-1].upper()
	else:
		return inet_ntoa(info[20:24])


def getIfConfig(ifname):
	ifreq = {"ifname": ifname}
	infos = {}
	sock = socket(AF_INET, SOCK_DGRAM)
	# Offsets defined in /usr/include/linux/sockios.h on linux 2.6.
	infos["addr"] = 0x8915  # SIOCGIFADDR
	infos["brdaddr"] = 0x8919  # SIOCGIFBRDADDR
	infos["hwaddr"] = 0x8927  # SIOCSIFHWADDR
	infos["netmask"] = 0x891b  # SIOCGIFNETMASK
	try:
		for k, v in infos.items():
			ifreq[k] = _ifinfo(sock, v, ifname)
	except Exception as ex:
		print("[About] getIfConfig Ex: %s" % str(ex))
		pass
	sock.close()
	return ifreq


def getIfTransferredData(ifname):
	lines = fileReadLines("/proc/net/dev", source=MODULE_NAME)
	if lines:
		for line in lines:
			if ifname in line:
				data = line.split("%s:" % ifname)[1].split()
				rx_bytes, tx_bytes = (data[0], data[8])
				return rx_bytes, tx_bytes


def getVersionString():
	return getImageVersionString()


def getImageVersionString():
	try:
		if isfile('/var/lib/opkg/status'):
			st = stat('/var/lib/opkg/status')
		tm = time.localtime(st.st_mtime)
		if tm.tm_year >= 2011:
			return time.strftime("%Y-%m-%d %H:%M:%S", tm)
	except:
		pass
	return _("unavailable")

# WW -placeholder for BC purposes, commented out for the moment in the Screen


def getFlashDateString():
	return _("unknown")


def getBuildDateString():
	version = fileReadLine("/etc/version", source=MODULE_NAME)
	if version is None:
		return _("Unknown")
	return "%s-%s-%s" % (version[:4], version[4:6], version[6:8])


def getUpdateDateString():
	try:
		from glob import glob
		build = [x.split("-")[-2:-1][0][-8:] for x in open(glob("/var/lib/opkg/info/openpli-bootlogo.control")[0], "r") if x.startswith("Version:")][0]
		if build.isdigit():
			return "%s-%s-%s" % (build[:4], build[4:6], build[6:])
	except:
		pass
	return _("unknown")


def getEnigmaVersionString():
	import enigma
	enigma_version = enigma.getEnigmaVersionString()
	if '-(no branch)' in enigma_version:
		enigma_version = enigma_version[:-12]
	return enigma_version


def getGStreamerVersionString():
	try:
		from glob import glob
		gst = [x.split("Version: ") for x in open(glob("/var/lib/opkg/info/gstreamer[0-9].[0-9].control")[0], "r") if x.startswith("Version:")][0]
		return "%s" % gst[1].split("+")[0].replace("\n", "")
	except:
		return _("Not Installed")


def getFFmpegVersionString():
	lines = fileReadLines("/var/lib/opkg/info/ffmpeg.control", source=MODULE_NAME)
	if lines:
		for line in lines:
			if line[0:8] == "Version:":
				return line[9:].split("+")[0]
	return _("Not Installed")


def getKernelVersionString():
	version = fileReadLine("/proc/version", source=MODULE_NAME)
	if version is None:
		return _("Unknown")
	return version.split(" ", 4)[2].split("-", 2)[0]


def getHardwareTypeString():
	return HardwareInfo().get_device_string()


def getImageTypeString():
	try:
		image_type = open("/etc/issue").readlines()[-2].strip()[:-6]
		return image_type.capitalize()
	except:
		return _("undefined")


def getCPUInfoString():
	cpu_count = 0
	cpu_speed = 0
	processor = ""
	lines = fileReadLines("/proc/cpuinfo", source=MODULE_NAME)
	if lines:
		for line in lines:
			line = [x.strip() for x in line.strip().split(":", 1)]
			if not processor and line[0] in ("system type", "model name", "Processor"):
				processor = line[1].split()[0]
			elif not cpu_speed and line[0] == "cpu MHz":
				cpu_speed = "%1.0f" % float(line[1])
			elif line[0] == "processor":
				cpu_count += 1
		if processor.startswith("ARM") and isfile("/proc/stb/info/chipset"):
			processor = "%s (%s)" % (fileReadLine("/proc/stb/info/chipset", "", source=MODULE_NAME).upper(), processor)
		if not cpu_speed:
			cpu_speed = fileReadLine("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", source=MODULE_NAME)
			if cpu_speed is None:
				try:
					cpu_speed = int(int(binascii.hexlify(open('/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency', 'rb').read()), 16) / 100000000) * 100
				except:
					print("[About] Read /sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency failed.")
					cpu_speed = "-"
			else:
				cpu_speed = int(cpu_speed) / 1000

		temperature = None
		freq = _("MHz")
		if isfile("/proc/stb/fp/temp_sensor_avs"):
			temperature = fileReadLine("/proc/stb/fp/temp_sensor_avs", source=MODULE_NAME)
		elif isfile("/proc/stb/power/avs"):
			temperature = fileReadLine("/proc/stb/power/avs", source=MODULE_NAME)
#		elif isfile("/proc/stb/fp/temp_sensor"):
#			temperature = fileReadLine("/proc/stb/fp/temp_sensor", source=MODULE_NAME)
#		elif isfile("/proc/stb/sensors/temp0/value"):
#			temperature = fileReadLine("/proc/stb/sensors/temp0/value", source=MODULE_NAME)
#		elif isfile("/proc/stb/sensors/temp/value"):
#			temperature = fileReadLine("/proc/stb/sensors/temp/value", source=MODULE_NAME)
		elif isfile("/sys/devices/virtual/thermal/thermal_zone0/temp"):
			temperature = fileReadLine("/sys/devices/virtual/thermal/thermal_zone0/temp", source=MODULE_NAME)
			if temperature:
				temperature = int(temperature) / 1000
		elif isfile("/sys/class/thermal/thermal_zone0/temp"):
			temperature = fileReadLine("/sys/class/thermal/thermal_zone0/temp", source=MODULE_NAME)
			if temperature:
				temperature = int(temperature) / 1000
		elif isfile("/proc/hisi/msp/pm_cpu"):
			lines = fileReadLines("/proc/hisi/msp/pm_cpu", source=MODULE_NAME)
			if lines:
				for line in lines:
					if "temperature = " in line:
						temperature = line.split("temperature = ")[1].split()[0]
		if temperature:
			degree = u"\u00B0"
			if not isinstance(degree, str):
				degree = degree.encode("UTF-8", errors="ignore")
			return "%s %s MHz (%s) %s%sC" % (processor, cpu_speed, ngettext("%d core", "%d cores", cpu_count) % cpu_count, temperature, degree)
		return "%s %s MHz (%s)" % (processor, cpu_speed, ngettext("%d core", "%d cores", cpu_count) % cpu_count)
def getSystemTemperature():
	temperature = ""
	if isfile("/proc/stb/sensors/temp0/value"):
		temperature = fileReadLine("/proc/stb/sensors/temp0/value", source=MODULE_NAME)
	elif isfile("/proc/stb/sensors/temp/value"):
		temperature = fileReadLine("/proc/stb/sensors/temp/value", source=MODULE_NAME)
	elif isfile("/proc/stb/fp/temp_sensor"):
		temperature = fileReadLine("/proc/stb/fp/temp_sensor", source=MODULE_NAME)
	if temperature:
		return "%s%s C" % (temperature, u"\u00B0")
	return temperature


def getDriverInstalledDate():
	def extractDate(value):
		match = search('[0-9]{8}', value)
		if match:
			return match[0]
		else:
			return value
	filenames = glob("/var/lib/opkg/info/*dvb-modules*.control")
	if filenames:
		lines = fileReadLines(filenames[0], source=MODULE_NAME)
		if lines:
			for line in lines:
				if line[0:8] == "Version:":
					return extractDate(line)
	filenames = glob("/var/lib/opkg/info/*dvb-proxy*.control")
	if filenames:
		lines = fileReadLines(filenames[0], source=MODULE_NAME)
		if lines:
			for line in lines:
				if line[0:8] == "Version:":
					return extractDate(line)
	filenames = glob("/var/lib/opkg/info/*platform-util*.control")
	if filenames:
		lines = fileReadLines(filenames[0], source=MODULE_NAME)
		if lines:
			for line in lines:
				if line[0:8] == "Version:":
					return extractDate(line)
	return _("Unknown")


def getPythonVersionString():
	try:
		return pyversion.split(' ')[0]
	except:
		return _("Unknown")


def GetIPsFromNetworkInterfaces():
	structSize = 40 if maxsize > 2 ** 32 else 32
	sock = socket(AF_INET, SOCK_DGRAM)
	maxPossible = 8  # Initial value.
	while True:
		_bytes = maxPossible * structSize
		names = array("B")
		for index in range(_bytes):
			names.append(0)
		outbytes = unpack("iL", ioctl(sock.fileno(), 0x8912, pack("iL", _bytes, names.buffer_info()[0])))[0]  # 0x8912 = SIOCGIFCONF
		if outbytes == _bytes:
			maxPossible *= 2
		else:
			break
	ifaces = []
	for index in range(0, outbytes, structSize):
		ifaceName = names.tobytes()[index:index + 16].decode().split("\0", 1)[0]  # PY3
		# ifaceName = str(names.tolist[index:index + 16]).split("\0", 1)[0] # PY2
		if ifaceName != "lo":
			ifaces.append((ifaceName, inet_ntoa(names[index + 20:index + 24])))
	return ifaces


def getBoxUptime():
	upTime = fileReadLine("/proc/uptime", source=MODULE_NAME)
	if upTime is None:
		return "-"
	secs = int(upTime.split(".")[0])
	times = []
	if secs > 86400:
		days = secs // 86400
		secs = secs % 86400
		times.append(ngettext("%d Day", "%d Days", days) % days)
	h = secs // 3600
	m = (secs % 3600) // 60
	times.append(ngettext("%d Hour", "%d Hours", h) % h)
	times.append(ngettext("%d Minute", "%d Minutes", m) % m)
	return " ".join(times)


def getGlibcVersion():
	process = Popen(("/lib/libc.so.6"), stdout=PIPE, stderr=PIPE, universal_newlines=True)
	stdout, stderr = process.communicate()
	if process.returncode == 0:
		for line in stdout.split("\n"):
			if line.startswith("GNU C Library"):
				data = line.split()[-1]
				if data.endswith("."):
					data = data[0:-1]
				return data
	print("[About] Get glibc version failed.")
	return _("Unknown")


def getGccVersion():
	process = Popen(("/lib/libc.so.6"), stdout=PIPE, stderr=PIPE, universal_newlines=True)
	stdout, stderr = process.communicate()
	if process.returncode == 0:
		for line in stdout.split("\n"):
			if line.startswith("Compiled by GNU CC version"):
				data = line.split()[-1]
				if data.endswith("."):
					data = data[0:-1]
				return data
	print("[About] Get gcc version failed.")
	return _("Unknown")


def getOpenSSLVersion():
	lines = fileReadLines("/var/lib/opkg/info/openssl.control", source=MODULE_NAME)
	if lines:
		for line in lines:
			if line[0:8] == "Version:":
				return line[9:].split("+")[0]
	return _("Not Installed")


# For modules that do "from About import about"
about = modules[__name__]
