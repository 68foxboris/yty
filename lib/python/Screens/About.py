from Screens.Screen import Screen
from six import ensure_str, text_type
from Screens.MessageBox import MessageBox
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Harddisk import harddiskmanager
from Components.NimManager import nimmanager
from Components.About import about
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.SystemInfo import SystemInfo

from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.Console import Console
from Components.Pixmap import MultiPixmap, Pixmap
from Components.Network import iNetwork
from Tools.Directories import SCOPE_PLUGINS, resolveFilename, isPluginInstalled
from Tools.StbHardware import getFPVersion
from Tools.Geolocation import geolocation
from enigma import eTimer, eLabel, eConsoleAppContainer, getDesktop, eGetEnigmaDebugLvl

from Components.GUIComponent import GUIComponent
from skin import applySkinFactor, parameters, parseScale

from time import strftime

import os
import glob

API_GITHUB = 0
API_GITLAB = 1

class About(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("About"))
		self["key_green"] = Button(_("Translations"))
		self["key_red"] = Button(_("Latest Commits"))
		self["key_yellow"] = Button(_("Dmesg Info"))
		self["key_blue"] = Button(_("Memory Info"))

		hddsplit = parameters.get("AboutHddSplit", 1)

		AboutText = _("Hardware: ") + about.getHardwareTypeString() + "\n"
		cpu = about.getCPUInfoString()
		AboutText += _("CPU: ") + cpu + "\n"

		AboutText += _("Image: ") + about.getImageTypeString() + "\n"
		AboutText += _("Last update: ") + about.getUpdateDateString() + "\n"

		# [WanWizard] Removed until we find a reliable way to determine the installation date
		# AboutText += _("Installed: ") + about.getFlashDateString() + "\n"

		EnigmaVersion = about.getEnigmaVersionString()
		EnigmaVersion = EnigmaVersion.rsplit("-", EnigmaVersion.count("-") - 2)
		if len(EnigmaVersion) == 3:
			EnigmaVersion = EnigmaVersion[0] + " (" + EnigmaVersion[2] + "-" + EnigmaVersion[1] + ")"
		else:
			EnigmaVersion = EnigmaVersion[0] + " (" + EnigmaVersion[1] + ")"
		EnigmaVersion = _("Enigma version: ") + EnigmaVersion
		self["EnigmaVersion"] = StaticText(EnigmaVersion)
		AboutText += "\n" + EnigmaVersion + "\n"

		AboutText += _("Build date: ") + about.getBuildDateString() + "\n"
		AboutText += _("DVB driver version: ") + about.getDriverInstalledDate() + "\n"

		AboutText += _("Kernel version: ") + about.getKernelVersionString() + "\n"

		GStreamerVersion = _("GStreamer version: ") + about.getGStreamerVersionString().replace("GStreamer", "")
		self["GStreamerVersion"] = StaticText(GStreamerVersion)
		AboutText += GStreamerVersion + "\n"

		FFmpegVersion = _("FFmpeg version: ") + about.getFFmpegVersionString()
		self["FFmpegVersion"] = StaticText(FFmpegVersion)
		AboutText += FFmpegVersion + "\n"
		AboutText += _("Python version: ") + about.getPythonVersionString() + "\n"
		AboutText += _("GCC version: ") + about.getGccVersion() + "\n"
		AboutText += _("OpenSSL version: ") + about.getOpenSSLVersion() + "\n"
		AboutText += _("Enigma (re)starts: %d\n") % config.misc.startCounter.value
		AboutText += _("Enigma2 debug level: %d\n") % eGetEnigmaDebugLvl() + "\n"

		fp_version = getFPVersion()
		if fp_version is None:
			fp_version = ""
		else:
			fp_version = _("Frontprocessor version: %s") % fp_version
			AboutText += fp_version
			self["FPVersion"] = StaticText(fp_version)

		if SystemInfo["HasHDMI-CEC"] and config.hdmicec.enabled.value:
			address = config.hdmicec.fixed_physical_address.value if config.hdmicec.fixed_physical_address.value != "0.0.0.0" else _("No fixed address set")
			AboutText += "\n" + _("HDMI-CEC Enabled") + ": " + address
		else:
			hdmicec_disabled = _("Disabled")
			AboutText += "\n" + _("HDMI-CEC %s") % hdmicec_disabled

		AboutText += "\n" + _('Skin & Resolution: %s (%sx%s)\n') % (config.skin.primary_skin.value.split('/')[0], getDesktop(0).size().width(), getDesktop(0).size().height())

		servicemp3 = _("ServiceMP3. IPTV recording (Yes).")
		servicehisilicon = _("ServiceHisilicon. IPTV recording (No). (Recommended ServiceMP3).")
		exteplayer3 = _("ServiceApp-ExtEplayer3. IPTV recording (No). (Recommended ServiceMP3).")
		gstplayer = _("ServiceApp-GstPlayer. IPTV recording (No). (Recommended ServiceMP3).")
		if isPluginInstalled("ServiceApp"):
			if isPluginInstalled("ServiceMP3"):
				if config.plugins.serviceapp.servicemp3.replace.value and config.plugins.serviceapp.servicemp3.player.value == "exteplayer3":
					player = "%s" % exteplayer3
				else:
					player = "%s" % gstplayer
				if not config.plugins.serviceapp.servicemp3.replace.value:
					player = "%s" % servicemp3
			elif isPluginInstalled("ServiceHisilicon"):
				if config.plugins.serviceapp.servicemp3.replace.value and config.plugins.serviceapp.servicemp3.player.value == "exteplayer3":
					player = "%s" % exteplayer3
				else:
					player = "%s" % gstplayer
				if not config.plugins.serviceapp.servicemp3.replace.value:
					player = "%s" % servicehisilicon
			else:
				player = _("Not installed")
		else:
			if isPluginInstalled("ServiceMP3"):
				player = "%s" % servicemp3
			elif isPluginInstalled("ServiceHisilicon"):
				player = "%s" % servicehisilicon
			else:
				player = _("Not installed")
		AboutText += _("Player: %s") % player + "\n"

		AboutText += "\n"
		AboutText += _("Uptime: ") + about.getBoxUptime() + "\n"




		self["TunerHeader"] = StaticText(_("Detected NIMs:"))
		AboutText += "\n" + _("Detected NIMs:") + "\n"

		nims = nimmanager.nimListCompressed()
		for count in range(len(nims)):
			if count < 4:
				self["Tuner" + str(count)] = StaticText(nims[count])
			else:
				self["Tuner" + str(count)] = StaticText("")
			AboutText += nims[count] + "\n"

		self["HDDHeader"] = StaticText(_("Detected storage devices:"))
		AboutText += "\n" + _("Detected storage devices:") + "\n"

		hddlist = harddiskmanager.HDDList()
		hddinfo = ""
		if hddlist:
			formatstring = hddsplit and "%s:%s, %.1f %s %s" or "%s\n(%s, %.1f %s %s)"
			for count in range(len(hddlist)):
				if hddinfo:
					hddinfo += "\n"
				hdd = hddlist[count][1]
				if int(hdd.free()) > 1024:
					hddinfo += formatstring % (hdd.model(), hdd.capacity(), hdd.free() / 1024.0, _("GB"), _("free"))
				else:
					hddinfo += formatstring % (hdd.model(), hdd.capacity(), hdd.free(), _("MB"), _("free"))
		else:
			hddinfo = _("none")
		self["hddA"] = StaticText(hddinfo)
		AboutText += hddinfo + "\n\n" + _("Network Info:")
		for x in about.GetIPsFromNetworkInterfaces():
			AboutText += "\n" + x[0] + ": " + x[1]

		self["AboutScrollLabel"] = ScrollLabel(AboutText)
		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"red": self.showCommits,
			"green": self.showTranslationInfo,
			"blue": self.showMemoryInfo,
			"yellow": self.showTroubleshoot,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})

	def showTranslationInfo(self):
		self.session.open(TranslationInfo)

	def showCommits(self):
		self.session.open(CommitInfo)

	def showMemoryInfo(self):
		self.session.open(MemoryInfo)

	def showTroubleshoot(self):
		self.session.open(Troubleshoot)


class Geolocation(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Geolocation"))
		self.setTitle(_("Geolocation Information"))

		GeolocationText = _("Information about your Geolocation data") + "\n"
		self["key_red"] = Button(_("Close"))
		GeolocationText += "\n"

		try:
			geolocationData = geolocation.getGeolocationData(fields="continent,country,regionName,city,timezone,currency,lat,lon", useCache=True)
			continent = geolocationData.get("continent", None)
			if isinstance(continent, text_type):
				continent = ensure_str(continent.encode(encoding="UTF-8", errors="ignore"))
			if continent != None:
				GeolocationText += _("Continent: ") + "\t" + continent + "\n"

			country = geolocationData.get("country", None)
			if isinstance(country, text_type):
				country = ensure_str(country.encode(encoding="UTF-8", errors="ignore"))
			if country != None:
				GeolocationText += _("Country: ") + "\t" + country + "\n"

			state = geolocationData.get("regionName", None)
			if isinstance(state, text_type):
				state = ensure_str(state.encode(encoding="UTF-8", errors="ignore"))
			if state != None:
				GeolocationText += _("RegionName: ") + "\t" + state + "\n"

			city = geolocationData.get("city", None)
			if isinstance(city, text_type):
				city = ensure_str(city.encode(encoding="UTF-8", errors="ignore"))
			if city != None:
				GeolocationText += _("City: ") + "\t" + city + "\n"

			GeolocationText += "\n"

			timezone = geolocationData.get("timezone", None)
			if isinstance(timezone, text_type):
				timezone = ensure_str(timezone.encode(encoding="UTF-8", errors="ignore"))
			if timezone != None:
				GeolocationText += _("Timezone: ") + "\t" + timezone + "\n"

			currency = geolocationData.get("currency", None)
			if isinstance(currency, text_type):
				currency = ensure_str(currency.encode(encoding="UTF-8", errors="ignore"))
			if currency != None:
				GeolocationText += _("Currency: ") + "\t" + currency + "\n"

			GeolocationText += "\n"

			latitude = geolocationData.get("lat", None)
			if str(float(latitude)) != None:
				GeolocationText += _("Latitude: ") + "\t" + str(float(latitude)) + "\n"

			longitude = geolocationData.get("lon", None)
			if str(float(longitude)) != None:
				GeolocationText += _("Longitude: ") + "\t" + str(float(longitude)) + "\n"
			self["AboutScrollLabel"] = ScrollLabel(GeolocationText)
		except Exception as err:
			self["AboutScrollLabel"] = ScrollLabel(_("Requires internet connection"))

		self["key_red"] = Button(_("Close"))

		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})



class Devices(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		screentitle = _("Devices")
		title = screentitle
		Screen.setTitle(self, title)
		self["TunerHeader"] = StaticText(_("Detected tuners:"))
		self["HDDHeader"] = StaticText(_("Detected devices:"))
		self["MountsHeader"] = StaticText(_("Network servers:"))
		self["nims"] = StaticText()
		for count in (0, 1, 2, 3):
			self["Tuner" + str(count)] = StaticText("")
		self["hdd"] = StaticText()
		self["mounts"] = StaticText()
		self.list = []
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.populate2)
		self["key_red"] = Button(_("Close"))
		self["actions"] = ActionMap(["SetupActions", "ColorActionsAbout", "TimerEditActions"], {
			"cancel": self.close,
			"red": self.close,
			"save": self.close,
		})
		self.onLayoutFinish.append(self.populate)

	def populate(self):
		self.mountinfo = ''
		self["actions"].setEnabled(False)
		scanning = _("Please wait while scanning for devices...")
		self["nims"].setText(scanning)
		for count in (0, 1, 2, 3):
			self["Tuner" + str(count)].setText(scanning)
		self["hdd"].setText(scanning)
		self['mounts'].setText(scanning)
		self.activityTimer.start(1)

	def populate2(self):
		self.activityTimer.stop()
		self.Console = Console()
		niminfo = ""
		nims = nimmanager.nimListCompressed()
		for count in range(len(nims)):
			if niminfo:
				niminfo += "\n"
			niminfo += nims[count]
		self["nims"].setText(niminfo)

		nims = nimmanager.nimList()
		if len(nims) <= 4 :
			for count in (0, 1, 2, 3):
				if count < len(nims):
					self["Tuner" + str(count)].setText(nims[count])
				else:
					self["Tuner" + str(count)].setText("")
		else:
			desc_list = []
			count = 0
			cur_idx = -1
			while count < len(nims):
				data = nims[count].split(":")
				idx = data[0].strip('Tuner').strip()
				desc = data[1].strip()
				if desc_list and desc_list[cur_idx]['desc'] == desc:
					desc_list[cur_idx]['end'] = idx
				else:
					desc_list.append({'desc' : desc, 'start' : idx, 'end' : idx})
					cur_idx += 1
				count += 1

			for count in (0, 1, 2, 3):
				if count < len(desc_list):
					if desc_list[count]['start'] == desc_list[count]['end']:
						text = "Tuner %s: %s" % (desc_list[count]['start'], desc_list[count]['desc'])
					else:
						text = "Tuner %s-%s: %s" % (desc_list[count]['start'], desc_list[count]['end'], desc_list[count]['desc'])
				else:
					text = ""

				self["Tuner" + str(count)].setText(text)

		self.hddlist = harddiskmanager.HDDList()
		self.list = []
		if self.hddlist:
			for count in range(len(self.hddlist)):
				hdd = self.hddlist[count][1]
				hddp = self.hddlist[count][0]
				if "ATA" in hddp:
					hddp = hddp.replace('ATA', '')
					hddp = hddp.replace('Internal', 'ATA Bus ')
				free = hdd.Totalfree()
				if ((float(free) / 1024) / 1024) >= 1:
					freeline = _("Free: ") + str(round(((float(free) / 1024) / 1024), 2)) + _("TB")
				elif (free / 1024) >= 1:
					freeline = _("Free: ") + str(round((float(free) / 1024), 2)) + _("GB")
				elif free >= 1:
					freeline = _("Free: ") + str(free) + _("MB")
				elif "Generic(STORAGE" in hddp:
					continue
				else:
					freeline = _("Free: ") + _("full")
				line = "%s      %s" % (hddp, freeline)
				self.list.append(line)
		self.list = '\n'.join(self.list)
		self["hdd"].setText(self.list)

		self.Console.ePopen("df -mh | grep -v '^Filesystem'", self.Stage1Complete)

	def Stage1Complete(self, result, retval, extra_args=None):
		result = result.replace('\n                        ', ' ').split('\n')
		self.mountinfo = ""
		for line in result:
			self.parts = line.split()
			if line and self.parts[0] and (self.parts[0].startswith('192') or self.parts[0].startswith('//192')):
				line = line.split()
				ipaddress = line[0]
				mounttotal = line[1]
				mountfree = line[3]
				if self.mountinfo:
					self.mountinfo += "\n"
				self.mountinfo += "%s (%sB, %sB %s)" % (ipaddress, mounttotal, mountfree, _("free"))

		if self.mountinfo:
			self["mounts"].setText(self.mountinfo)
		else:
			self["mounts"].setText(_('none'))
		self["actions"].setEnabled(True)


class SystemNetworkInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		screentitle = _("Network")
		title = screentitle
		Screen.setTitle(self, title)
		self.skinName = ["SystemNetworkInfo", "WlanStatus"]
		self["LabelBSSID"] = StaticText()
		self["LabelESSID"] = StaticText()
		self["LabelQuality"] = StaticText()
		self["LabelSignal"] = StaticText()
		self["LabelBitrate"] = StaticText()
		self["LabelEnc"] = StaticText()
		self["BSSID"] = StaticText()
		self["ESSID"] = StaticText()
		self["quality"] = StaticText()
		self["signal"] = StaticText()
		self["bitrate"] = StaticText()
		self["enc"] = StaticText()

		self["IFtext"] = StaticText()
		self["IF"] = StaticText()
		self["Statustext"] = StaticText()
		self["statuspic"] = MultiPixmap()
		self["statuspic"].setPixmapNum(1)
		self["statuspic"].show()
		self["devicepic"] = MultiPixmap()

		self["AboutScrollLabel"] = ScrollLabel()

		self.iface = None
		self.createscreen()
		self.iStatus = None

		if iNetwork.isWirelessInterface(self.iface):
			try:
				from Plugins.SystemPlugins.WirelessLan.Wlan import iStatus

				self.iStatus = iStatus
			except:
				pass
			self.resetList()
			self.onClose.append(self.cleanup)
		self["key_red"] = StaticText(_("Close"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown,
		})
		self.onLayoutFinish.append(self.updateStatusbar)

	def createscreen(self):
		self.AboutText = ""
		self.iface = "eth0"
		eth0 = about.getIfConfig('eth0')
		if 'addr' in eth0:
			self.AboutText += _("IP:") + "\t" + "\t" + eth0['addr'] + "\n"
			if 'netmask' in eth0:
				self.AboutText += _("Netmask:") + "\t" + eth0['netmask'] + "\n"
			if 'hwaddr' in eth0:
				self.AboutText += _("MAC:") + "\t" + "\t" + eth0['hwaddr'] + "\n"
			self.iface = 'eth0'

		eth1 = about.getIfConfig('eth1')
		if 'addr' in eth1:
			self.AboutText += _("IP:") + "\t" + "\t" + eth1['addr'] + "\n"
			if 'netmask' in eth1:
				self.AboutText += _("Netmask:") + "\t" + eth1['netmask'] + "\n"
			if 'hwaddr' in eth1:
				self.AboutText += _("MAC:") + "\t" + "\t" + eth1['hwaddr'] + "\n"
			self.iface = 'eth1'

		ra0 = about.getIfConfig('ra0')
		if 'addr' in ra0:
			self.AboutText += _("IP:") + "\t" + "\t" + ra0['addr'] + "\n"
			if 'netmask' in ra0:
				self.AboutText += _("Netmask:") + "\t" + ra0['netmask'] + "\n"
			if 'hwaddr' in ra0:
				self.AboutText += _("MAC:") + "\t" + "\t" + ra0['hwaddr'] + "\n"
			self.iface = 'ra0'

		wlan0 = about.getIfConfig('wlan0')
		if 'addr' in wlan0:
			self.AboutText += _("IP:") + "\t" + "\t" + wlan0['addr'] + "\n"
			if 'netmask' in wlan0:
				self.AboutText += _("Netmask:") + "\t" + wlan0['netmask'] + "\n"
			if 'hwaddr' in wlan0:
				self.AboutText += _("MAC:") + "\t" + "\t" + wlan0['hwaddr'] + "\n"
			self.iface = 'wlan0'

		wlan3 = about.getIfConfig('wlan3')
		if 'addr' in wlan3:
			self.AboutText += _("IP:") + "\t" + "\t" + wlan3['addr'] + "\n"
			if 'netmask' in wlan3:
				self.AboutText += _("Netmask:") + "\t" + wlan3['netmask'] + "\n"
			if 'hwaddr' in wlan3:
				self.AboutText += _("MAC:") + "\t" + "\t" + wlan3['hwaddr'] + "\n"
			self.iface = 'wlan3'

		rx_bytes, tx_bytes = about.getIfTransferredData(self.iface)
		self.AboutText += "\n" + _("Bytes received:") + "\t" + rx_bytes + "\n"
		self.AboutText += _("Bytes sent:") + "\t" + tx_bytes + "\n"

		geolocationData = geolocation.getGeolocationData(fields="isp,org,mobile,proxy,query", useCache=True)
		isp = geolocationData.get("isp", None)
		isporg = geolocationData.get("org", None)
		if isinstance(isp, text_type):
			isp = ensure_str(isp.encode(encoding="UTF-8", errors="ignore"))
		if isinstance(isporg, text_type):
			isporg = ensure_str(isporg.encode(encoding="UTF-8", errors="ignore"))
		self.AboutText += "\n"
		if isp != None:
			if isporg != None:
				self.AboutText += _("ISP: ") + "\t" + "\t" + isp + " " + (isporg) + "\n"
			else:
				self.AboutText += "\n" + _("ISP: ") + "\t" + "\t" + isp + "\n"

		mobile = geolocationData.get("mobile", False)
		if mobile:
			self.AboutText += _("Mobile: ") + "\t" + "\t" + _("Yes") + "\n"
		else:
			self.AboutText += _("Mobile: ") + "\t" + "\t" + _("No") + "\n"

		proxy = geolocationData.get("proxy", False)
		if proxy:
			self.AboutText += _("Proxy: ") + "\t" + "\t" + _("Yes") + "\n"
		else:
			self.AboutText += _("Proxy: ") + "\t" + "\t" + _("No") + "\n"

		publicip = geolocationData.get("query", None)
		if str(publicip) != "":
			self.AboutText += _("Public IP: ") + "\t" + "\t" + str(publicip) + "\n" + "\n"

		self.console = Console()
		self.console.ePopen('ethtool %s' % self.iface, self.SpeedFinished)

	def SpeedFinished(self, result, retval, extra_args):
		result_tmp = str(result).split('\n')
		for line in result_tmp:
			if 'Speed:' in line:
				speed = line.split(': ')[1][:-4]
				self.AboutText += _("Speed:") + "\t" + speed + _('Mb/s')

		hostname = open('/proc/sys/kernel/hostname').read()
		self.AboutText += "\n" + _("Hostname:") + "\t" + hostname + "\n"
		self["AboutScrollLabel"].setText(self.AboutText)

	def cleanup(self):
		if self.iStatus:
			self.iStatus.stopWlanConsole()

	def resetList(self):
		if self.iStatus:
			self.iStatus.getDataForInterface(self.iface, self.getInfoCB)

	def getInfoCB(self, data, status):
		self.LinkState = None
		if data != None and data:
			if status != None:
# getDataForInterface()->iwconfigFinished() in
# Plugins/SystemPlugins/WirelessLan/Wlan.py sets fields to boolean False
# if there is no info for them, so we need to check that possibility
# for each status[self.iface] field...
#
				if self.iface == 'wlan0' or self.iface == 'wlan3' or self.iface == 'ra0':
# accesspoint is used in the "enc" code too, so we get it regardless
#
					if not status[self.iface]["accesspoint"]:
						accesspoint = _("Unknown")
					else:
						if status[self.iface]["accesspoint"] == "Not-Associated":
							accesspoint = _("Not-Associated")
							essid = _("No connection")
						else:
							accesspoint = status[self.iface]["accesspoint"]
					if 'BSSID' in self:
						self.AboutText += _('Accesspoint:') + '\t' + accesspoint + '\n'

					if 'ESSID' in self:
						if not status[self.iface]["essid"]:
							essid = _("Unknown")
						else:
							if status[self.iface]["essid"] == "off":
								essid = _("No connection")
							else:
								essid = status[self.iface]["essid"]
						self.AboutText += _('SSID:') + '\t' + essid + '\n'

					if 'quality' in self:
						if not status[self.iface]["quality"]:
							quality = _("Unknown")
						else:
							quality = status[self.iface]["quality"]
						self.AboutText += _('Link quality:') + '\t' + quality + '\n'

					if 'bitrate' in self:
						if not status[self.iface]["bitrate"]:
							bitrate = _("Unknown")
						else:
							if status[self.iface]["bitrate"] == '0':
								bitrate = _("Unsupported")
							else:
								bitrate = str(status[self.iface]["bitrate"]) + " Mb/s"
						self.AboutText += _('Bitrate:') + '\t' + bitrate + '\n'

					if 'signal' in self:
						if not status[self.iface]["signal"]:
							signal = _("Unknown")
						else:
							signal = status[self.iface]["signal"]
						self.AboutText += _('Signal strength:') + '\t' + str(signal) + '\n'

					if 'enc' in self:
						if not status[self.iface]["encryption"]:
							encryption = _("Unknown")
						else:
							if status[self.iface]["encryption"] == "off":
								if accesspoint == "Not-Associated":
									encryption = _("Disabled")
								else:
									encryption = _("Unsupported")
							else:
								encryption = _("Enabled")
						self.AboutText += _('Encryption:') + '\t' + encryption + '\n'

					if ((status[self.iface]["essid"] and status[self.iface]["essid"] == "off") or
					    not status[self.iface]["accesspoint"] or
					    status[self.iface]["accesspoint"] == "Not-Associated"):
						self.LinkState = False
						self["statuspic"].setPixmapNum(1)
						self["statuspic"].show()
					else:
						self.LinkState = True
						iNetwork.checkNetworkState(self.checkNetworkCB)
					self["AboutScrollLabel"].setText(self.AboutText)

	def exit(self):
		self.close(True)

	def updateStatusbar(self):
		self["IFtext"].setText(_("Network:"))
		self["IF"].setText(iNetwork.getFriendlyAdapterName(self.iface))
		self["Statustext"].setText(_("Link:"))
		if iNetwork.isWirelessInterface(self.iface):
			self["devicepic"].setPixmapNum(1)
			try:
				self.iStatus.getDataForInterface(self.iface, self.getInfoCB)
			except:
				self["statuspic"].setPixmapNum(1)
				self["statuspic"].show()
		else:
			iNetwork.getLinkState(self.iface, self.dataAvail)
			self["devicepic"].setPixmapNum(0)
		self["devicepic"].show()

	def dataAvail(self, data):
		self.LinkState = None
		for line in data.splitlines():
			line = line.strip()
			if 'Link detected:' in line:
				if "yes" in line:
					self.LinkState = True
				else:
					self.LinkState = False
		if self.LinkState:
			iNetwork.checkNetworkState(self.checkNetworkCB)
		else:
			self["statuspic"].setPixmapNum(1)
			self["statuspic"].show()

	def checkNetworkCB(self, data):
		try:
			if iNetwork.getAdapterAttribute(self.iface, "up") is True:
				if self.LinkState is True:
					if data <= 2:
						self["statuspic"].setPixmapNum(0)
					else:
						self["statuspic"].setPixmapNum(1)
				else:
					self["statuspic"].setPixmapNum(1)
			else:
				self["statuspic"].setPixmapNum(1)
			self["statuspic"].show()
		except:
			pass


class SystemMemoryInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		screentitle = _("Memory")
		title = screentitle
		Screen.setTitle(self, title)
		self.skinName = ["SystemMemoryInfo", "About"]
		self["AboutScrollLabel"] = ScrollLabel()
		self["key_red"] = Button(_("Close"))
		self["actions"] = ActionMap(["SetupActions", "ColorActionsAbout"], {
			"cancel": self.close,
			"ok": self.close,
			"red": self.close,
		})

		out_lines = open("/proc/meminfo").readlines()
		self.AboutText = _("RAM") + '\n\n'
		RamTotal = "-"
		RamFree = "-"
		for lidx in range(len(out_lines) - 1):
			tstLine = out_lines[lidx].split()
			if "MemTotal:" in tstLine:
				MemTotal = out_lines[lidx].split()
				self.AboutText += _("Total memory:") + "\t" + "\t" + MemTotal[1] + "\n"
			if "MemFree:" in tstLine:
				MemFree = out_lines[lidx].split()
				self.AboutText += _("Free memory:") + "\t" + "\t" + MemFree[1] + "\n"
			if "Buffers:" in tstLine:
				Buffers = out_lines[lidx].split()
				self.AboutText += _("Buffers:") + "\t" + "\t" + Buffers[1] + "\n"
			if "Cached:" in tstLine:
				Cached = out_lines[lidx].split()
				self.AboutText += _("Cached:") + "\t" + "\t" + Cached[1] + "\n"
			if "SwapTotal:" in tstLine:
				SwapTotal = out_lines[lidx].split()
				self.AboutText += _("Total swap:") + "\t" + "\t" + SwapTotal[1] + "\n"
			if "SwapFree:" in tstLine:
				SwapFree = out_lines[lidx].split()
				self.AboutText += _("Free swap:") + "\t" + "\t" + SwapFree[1] + "\n\n"

		self["actions"].setEnabled(False)
		self.Console = Console()
		self.Console.ePopen("df -mh / | grep -v '^Filesystem'", self.Stage1Complete2)

	def Stage1Complete2(self, result, retval, extra_args=None):
		flash = str(result).replace('\n', '')
		flash = flash.split()
		RamTotal = flash[1]
		RamFree = flash[3]

		self.AboutText += _("Total:") + "\t" + "\t" + RamTotal + "\n"
		self.AboutText += _("Free:") + "\t" + "\t" + RamFree + "\n\n"

		self["AboutScrollLabel"].setText(self.AboutText)
		self["actions"].setEnabled(True)


class TranslationInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Translation"))
		# don't remove the string out of the _(), or it can't be "translated" anymore.

		# TRANSLATORS: Add here whatever should be shown in the "translator" about screen, up to 6 lines (use \n for newline)
		info = _("TRANSLATOR_INFO")

		if info == "TRANSLATOR_INFO":
			info = "(N/A)"

		infolines = _("").split("\n")
		infomap = {}
		for x in infolines:
			l = x.split(': ')
			if len(l) != 2:
				continue
			(type, value) = l
			infomap[type] = value
		print(infomap)
		self["key_red"] = Button(_("Cancel"))
		self["TranslationInfo"] = StaticText(info)

		translator_name = infomap.get("Language-Team", "none")
		if translator_name == "none":
			translator_name = infomap.get("Last-Translator", "")

		self["TranslatorName"] = StaticText(translator_name)

		self["actions"] = ActionMap(["SetupActions"], {
			"cancel": self.close,
			"ok": self.close,
		})


class CommitInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Latest Commits"))
		self.skinName = ["CommitInfo", "About"]
		self["AboutScrollLabel"] = ScrollLabel(_("Please wait"))

		self["actions"] = ActionMap(["SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown,
			"left": self.left,
			"right": self.right
		})

		self["key_red"] = Button(_("Cancel"))

		# get the branch to display from the Enigma version
		try:
			branch = "?sha=" + "-".join(about.getEnigmaVersionString().split("-")[3:])
		except:
			branch = ""
		branch_e2plugins = "?sha=python3"

		self.project = 0
		self.projects = [
			("https://api.github.com/repos/openpli/enigma2/commits" + branch, "Enigma2", API_GITHUB),
			("https://api.github.com/repos/openpli/openpli-oe-core/commits" + branch, "Openpli Oe Core", API_GITHUB),
			("https://api.github.com/repos/openpli/enigma2-plugins/commits" + branch_e2plugins, "Enigma2 Plugins", API_GITHUB),
			("https://api.github.com/repos/openpli/aio-grab/commits", "Aio Grab", API_GITHUB),
			("https://api.github.com/repos/openpli/enigma2-plugin-extensions-epgimport/commits", "Plugin EPGImport", API_GITHUB),
			("https://api.github.com/repos/littlesat/skin-PLiHD/commits", "Skin PLi HD", API_GITHUB),
			("https://api.github.com/repos/E2OpenPlugins/e2openplugin-OpenWebif/commits", "OpenWebif", API_GITHUB),
			("https://gitlab.openpli.org/api/v4/projects/5/repository/commits", "Hans settings", API_GITLAB)
		]
		self.cachedProjects = {}
		self.Timer = eTimer()
		self.Timer.callback.append(self.readGithubCommitLogs)
		self.Timer.start(50, True)

	def readGithubCommitLogs(self):
		url = self.projects[self.project][0]
		commitlog = ""
		from datetime import datetime
		from json import loads
		from urllib.request import urlopen
		try:
			commitlog += 80 * '-' + '\n'
			commitlog += url.split('/')[-2] + '\n'
			commitlog += 80 * '-' + '\n'
			try:
				# OpenPli 5.0 uses python 2.7.11 and here we need to bypass the certificate check
				from ssl import _create_unverified_context
				log = loads(urlopen(url, timeout=5, context=_create_unverified_context()).read())
			except:
				log = loads(urlopen(url, timeout=5).read())

			if self.projects[self.project][2] == API_GITHUB:
				for c in log:
					creator = c['commit']['author']['name']
					title = c['commit']['message']
					date = datetime.strptime(c['commit']['committer']['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%x %X')
					commitlog += date + ' ' + creator + '\n' + title + 2 * '\n'
			elif self.projects[self.project][2] == API_GITLAB:
				for c in log:
					creator = c['author_name']
					title = c['title']
					date = datetime.strptime(c['committed_date'], '%Y-%m-%dT%H:%M:%S.000%z').strftime('%x %X')
					commitlog += date + ' ' + creator + '\n' + title + 2 * '\n'

			self.cachedProjects[self.projects[self.project][1]] = commitlog
		except Exception as e:
			commitlog += _("Currently the commit log cannot be retrieved - please try later again.")
		self["AboutScrollLabel"].setText(commitlog)

	def updateCommitLogs(self):
		if self.projects[self.project][1] in self.cachedProjects:
			self["AboutScrollLabel"].setText(self.cachedProjects[self.projects[self.project][1]])
		else:
			self["AboutScrollLabel"].setText(_("Please wait"))
			self.Timer.start(50, True)

	def left(self):
		self.project = self.project == 0 and len(self.projects) - 1 or self.project - 1
		self.updateCommitLogs()

	def right(self):
		self.project = self.project != len(self.projects) - 1 and self.project + 1 or 0
		self.updateCommitLogs()


class MemoryInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.close,
			"ok": self.getMemoryInfo,
			"green": self.getMemoryInfo,
			"blue": self.clearMemory
		})

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Refresh"))
		self["key_blue"] = Label(_("Clear"))
		self['lmemtext'] = Label()
		self['lmemvalue'] = Label()
		self['rmemtext'] = Label()
		self['rmemvalue'] = Label()
		self['pfree'] = Label()
		self['pused'] = Label()
		self["slide"] = ProgressBar()
		self["slide"].setValue(100)

		self["params"] = MemoryInfoSkinParams()

		self['info'] = Label(_("This info is for developers only.\nFor normal users it is not relevant.\nPlease don't panic if you see values displayed looking suspicious!"))

		self.setTitle(_("Memory Info"))
		self.onLayoutFinish.append(self.getMemoryInfo)

	def getMemoryInfo(self):
		try:
			ltext = rtext = ""
			lvalue = rvalue = ""
			mem = 1
			free = 0
			rows_in_column = self["params"].rows_in_column
			for i, line in enumerate(open('/proc/meminfo', 'r')):
				s = line.strip().split(None, 2)
				if len(s) == 3:
					name, size, units = s
				elif len(s) == 2:
					name, size = s
					units = ""
				else:
					continue
				if name.startswith("MemTotal"):
					mem = int(size)
				if name.startswith("MemFree") or name.startswith("Buffers") or name.startswith("Cached"):
					free += int(size)
				if i < rows_in_column:
					ltext += "".join((name, "\n"))
					lvalue += "".join((size, " ", units, "\n"))
				else:
					rtext += "".join((name, "\n"))
					rvalue += "".join((size, " ", units, "\n"))
			self['lmemtext'].setText(ltext)
			self['lmemvalue'].setText(lvalue)
			self['rmemtext'].setText(rtext)
			self['rmemvalue'].setText(rvalue)
			self["slide"].setValue(int(100.0 * (mem - free) / mem + 0.25))
			self['pfree'].setText("%.1f %s" % (100. * free / mem, '%'))
			self['pused'].setText("%.1f %s" % (100. * (mem - free) / mem, '%'))
		except Exception as e:
			print("[About] getMemoryInfo FAIL:", e)

	def clearMemory(self):
		eConsoleAppContainer().execute("sync")
		open("/proc/sys/vm/drop_caches", "w").write("3")
		self.getMemoryInfo()


class MemoryInfoSkinParams(GUIComponent):
	def __init__(self):
		GUIComponent.__init__(self)
		self.rows_in_column = applySkinFactor(25)

	def applySkin(self, desktop, screen):
		if self.skinAttributes != None:
			attribs = []
			for (attrib, value) in self.skinAttributes:
				if attrib == "rowsincolumn":
					self.rows_in_column = parseScale(value)
			self.skinAttributes = attribs
		return GUIComponent.applySkin(self, desktop, screen)

	GUI_WIDGET = eLabel


class Troubleshoot(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Troubleshoot"))
		self["AboutScrollLabel"] = ScrollLabel(_("Please wait"))
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = Button()

		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActionsAbout"], {
			"cancel": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown,
			"moveUp": self["AboutScrollLabel"].homePage,
			"moveDown": self["AboutScrollLabel"].endPage,
			"left": self.left,
			"right": self.right,
			"red": self.red,
			"green": self.green,
		})

		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.appClosed)
		self.container.dataAvail.append(self.dataAvail)
		self.commandIndex = 0
		self.updateOptions()
		self.onLayoutFinish.append(self.run_console)

	def left(self):
		self.commandIndex = (self.commandIndex - 1) % len(self.commands)
		self.updateKeys()
		self.run_console()

	def right(self):
		self.commandIndex = (self.commandIndex + 1) % len(self.commands)
		self.updateKeys()
		self.run_console()

	def red(self):
		if self.commandIndex >= self.numberOfCommands:
			self.session.openWithCallback(self.removeAllLogfiles, MessageBox, _("Do you want to remove all the crash logfiles"), default=False)
		else:
			self.close()

	def green(self):
		if self.commandIndex >= self.numberOfCommands:
			try:
				os.remove(self.commands[self.commandIndex][4:])
			except:
				pass
			self.updateOptions()
		self.run_console()

	def removeAllLogfiles(self, answer):
		if answer:
			for fileName in self.getLogFilesList():
				try:
					os.remove(fileName)
				except:
					pass
			self.updateOptions()
			self.run_console()

	def appClosed(self, retval):
		if retval:
			self["AboutScrollLabel"].setText(_("An error occurred - Please try again later"))

	def dataAvail(self, data):
		self["AboutScrollLabel"].appendText(data.decode())

	def run_console(self):
		self["AboutScrollLabel"].setText("")
		self.setTitle("%s - %s" % (_("Troubleshoot"), self.titles[self.commandIndex]))
		command = self.commands[self.commandIndex]
		if command.startswith("cat "):
			try:
				self["AboutScrollLabel"].setText(open(command[4:], "r").read())
			except:
				self["AboutScrollLabel"].setText(_("Logfile does not exist anymore"))
		else:
			try:
				if self.container.execute(command):
					raise Exception("failed to execute: " + command)
			except Exception as e:
				self["AboutScrollLabel"].setText("%s\n%s" % (_("An error occurred - Please try again later"), e))

	def cancel(self):
		self.container.appClosed.remove(self.appClosed)
		self.container.dataAvail.remove(self.dataAvail)
		self.container = None
		self.close()

	def getDebugFilesList(self):
		import glob
		return [x for x in sorted(glob.glob("/home/root/enigma.*.debuglog"), key=lambda x: os.path.isfile(x) and os.path.getmtime(x))]

	def getLogFilesList(self):
		import glob
		home_root = "/home/root/enigma2_crash.log"
		tmp = "/tmp/enigma2_crash.log"
		return [x for x in sorted(glob.glob("/mnt/hdd/*.log"), key=lambda x: os.path.isfile(x) and os.path.getmtime(x))] + (os.path.isfile(home_root) and [home_root] or []) + (os.path.isfile(tmp) and [tmp] or [])

	def updateOptions(self):
		self.titles = ["dmesg", "ifconfig", "df", "top", "ps", "messages"]
		self.commands = ["dmesg", "ifconfig", "df -h", "top -n 1", "ps -l", "cat /var/volatile/log/messages"]
		install_log = "/home/root/autoinstall.log"
		if os.path.isfile(install_log):
				self.titles.append("%s" % install_log)
				self.commands.append("cat %s" % install_log)
		self.numberOfCommands = len(self.commands)
		fileNames = self.getLogFilesList()
		if fileNames:
			totalNumberOfLogfiles = len(fileNames)
			logfileCounter = 1
			for fileName in reversed(fileNames):
				self.titles.append("logfile %s (%s/%s)" % (fileName, logfileCounter, totalNumberOfLogfiles))
				self.commands.append("cat %s" % (fileName))
				logfileCounter += 1
		fileNames = self.getDebugFilesList()
		if fileNames:
			totalNumberOfLogfiles = len(fileNames)
			logfileCounter = 1
			for fileName in reversed(fileNames):
				self.titles.append("debug log %s (%s/%s)" % (fileName, logfileCounter, totalNumberOfLogfiles))
				self.commands.append("tail -n 2500 %s" % (fileName))
				logfileCounter += 1
		self.commandIndex = min(len(self.commands) - 1, self.commandIndex)
		self.updateKeys()

	def updateKeys(self):
		self["key_red"].setText(_("Close") if self.commandIndex < self.numberOfCommands else _("Remove all logfiles"))
		self["key_green"].setText(_("Refresh") if self.commandIndex < self.numberOfCommands else _("Remove this logfile"))
