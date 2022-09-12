from Components.config import config, ConfigSlider, ConfigSelection, ConfigYesNo, ConfigEnableDisable, ConfigOnOff, ConfigSubsection, ConfigBoolean, ConfigSelectionNumber, ConfigNothing, NoSave
from enigma import eAVSwitch, eDVBVolumecontrol, getDesktop
from Components.SystemInfo import SystemInfo
from Tools.HardwareInfo import HardwareInfo
import os

model = HardwareInfo().get_device_model()


class AVSwitch:
	def setInput(self, input):
		INPUT = {"ENCODER": 0, "SCART": 1, "AUX": 2}
		eAVSwitch.getInstance().setInput(INPUT[input])

	def setColorFormat(self, value):
		eAVSwitch.getInstance().setColorFormat(value)

	def setAspectRatio(self, value):
		eAVSwitch.getInstance().setAspectRatio(value)

	def setSystem(self, value):
		eAVSwitch.getInstance().setVideomode(value)

	def getOutputAspect(self):
		valstr = config.av.aspectratio.value
		if valstr in ("4_3_letterbox", "4_3_panscan"): # 4:3
			return (4, 3)
		elif valstr == "16_9": # auto ... 4:3 or 16:9
			try:
				print("[AVSwitch] Read /proc/stb/vmpeg/0/aspect")
				if "1" in open("/proc/stb/vmpeg/0/aspect", "r").read(): # 4:3
					return (4, 3)
			except IOError:
				print("[AVSwitch] Read /proc/stb/vmpeg/0/aspect failed.")
		elif valstr in ("16_9_always", "16_9_letterbox"): # 16:9
			pass
		elif valstr in ("16_10_letterbox", "16_10_panscan"): # 16:10
			return (16, 10)
		return (16, 9)

	def getFramebufferScale(self):
		aspect = self.getOutputAspect()
		fb_size = getDesktop(0).size()
		return (aspect[0] * fb_size.height(), aspect[1] * fb_size.width())

	def getAspectRatioSetting(self):
		valstr = config.av.aspectratio.value
		if valstr == "4_3_letterbox":
			val = 0
		elif valstr == "4_3_panscan":
			val = 1
		elif valstr == "16_9":
			val = 2
		elif valstr == "16_9_always":
			val = 3
		elif valstr == "16_10_letterbox":
			val = 4
		elif valstr == "16_10_panscan":
			val = 5
		elif valstr == "16_9_letterbox":
			val = 6
		return val

	def setAspectWSS(self, aspect=None):
		if not config.av.wss.value:
			value = 2 # auto(4:3_off)
		else:
			value = 1 # auto
		eAVSwitch.getInstance().setWSS(value)


def InitAVSwitch():
	config.av = ConfigSubsection()
	if model == "vuduo":
		config.av.yuvenabled = ConfigBoolean(default=False)
	else:
		config.av.yuvenabled = ConfigBoolean(default=True)
	colorformat_choices = {"cvbs": "CVBS"}

	# when YUV, Scart or S-Video is not support by HW, don't let the user select it
	if SystemInfo["HasYPbPr"]:
		colorformat_choices["yuv"] = "YPbPr"
	if SystemInfo["HasScart"]:
		colorformat_choices["rgb"] = "RGB"
	if SystemInfo["HasSVideo"]:
		colorformat_choices["svideo"] = "S-Video"

	config.av.colorformat = ConfigSelection(choices=colorformat_choices, default="cvbs")
	config.av.aspectratio = ConfigSelection(choices={
			"4_3_letterbox": _("4:3 Letterbox"),
			"4_3_panscan": _("4:3 PanScan"),
			"16_9": _("16:9"),
			"16_9_always": _("16:9 always"),
			"16_10_letterbox": _("16:10 Letterbox"),
			"16_10_panscan": _("16:10 PanScan"),
			"16_9_letterbox": _("16:9 Letterbox")},
			default="16_9")
	config.av.aspect = ConfigSelection(choices={
			"4_3": _("4:3"),
			"16_9": _("16:9"),
			"16_10": _("16:10"),
			"auto": _("Automatic")},
			default="auto")
	policy2_choices = {
	# TRANSLATORS: (aspect ratio policy: black bars on top/bottom) in doubt, keep english term.
	"letterbox": _("Letterbox"),
	# TRANSLATORS: (aspect ratio policy: cropped content on left/right) in doubt, keep english term
	"panscan": _("Pan&scan"),
	# TRANSLATORS: (aspect ratio policy: scale as close to fullscreen as possible)
	"scale": _("Just scale")}
	try:
		print("[AVSwitch] Read /proc/stb/video/policy2_choices")
		if "full" in open("/proc/stb/video/policy2_choices").read():
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, even if the content aspect ratio does not match the screen ratio)
			policy2_choices.update({"full": _("Full screen")})
	except:
		print("[AVSwitch] Read /proc/stb/video/policy2_choices failed.")
	try:
		print("[AVSwitch] Read /proc/stb/video/policy2_choices")
		if "auto" in open("/proc/stb/video/policy2_choices").read():
			# TRANSLATORS: (aspect ratio policy: automatically select the best aspect ratio mode)
			policy2_choices.update({"auto": _("Auto")})
	except:
		print("[AVSwitch] Read /proc/stb/video/policy2_choices failed.")
	config.av.policy_169 = ConfigSelection(choices=policy2_choices, default="scale")
	policy_choices = {
	# TRANSLATORS: (aspect ratio policy: black bars on left/right) in doubt, keep english term.
	"pillarbox": _("Pillarbox"),
	# TRANSLATORS: (aspect ratio policy: cropped content on left/right) in doubt, keep english term
	"panscan": _("Pan&scan"),
	# TRANSLATORS: (aspect ratio policy: scale as close to fullscreen as possible)
	"scale": _("Just scale")}
	try:
		print("[AVSwitch] Read /proc/stb/video/policy_choices")
		if "nonlinear" in open("/proc/stb/video/policy_choices").read():
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching the left/right)
			policy_choices.update({"nonlinear": _("Nonlinear")})
	except:
		print("[AVSwitch] Read /proc/stb/video/policy_choices failed.")
	try:
		print("[AVSwitch] Read /proc/stb/video/policy_choices")
		if "full" in open("/proc/stb/video/policy_choices").read():
			# TRANSLATORS: (aspect ratio policy: display as fullscreen, even if the content aspect ratio does not match the screen ratio)
			policy_choices.update({"full": _("Full screen")})
	except:
		print("[AVSwitch] Read /proc/stb/video/policy_choices failed.")
	try:
		print("[AVSwitch] Read /proc/stb/video/policy_choices")
		if "auto" in open("/proc/stb/video/policy_choices").read():
			# TRANSLATORS: (aspect ratio policy: automatically select the best aspect ratio mode)
			policy_choices.update({"auto": _("Auto")})
	except:
		print("[AVSwitch] Read /proc/stb/video/policy_choices failed.")
	config.av.policy_43 = ConfigSelection(choices=policy_choices, default="scale")
	config.av.tvsystem = ConfigSelection(choices={"pal": "PAL", "ntsc": "NTSC", "multinorm": "multinorm"}, default="pal")
	config.av.wss = ConfigEnableDisable(default=True)
	config.av.generalAC3delay = ConfigSelectionNumber(-1000, 1000, 5, default=0)
	config.av.generalPCMdelay = ConfigSelectionNumber(-1000, 1000, 5, default=0)
	config.av.vcrswitch = ConfigEnableDisable(default=False)

	iAVSwitch = AVSwitch()

	def setColorFormat(configElement):
		if model == "et6x00":
			map = {"cvbs": 3, "rgb": 3, "svideo": 2, "yuv": 3}
		elif model == "gb7356":
			map = {"cvbs": 0, "rgb": 3, "svideo": 2, "yuv": 3}
		else:
			map = {"cvbs": 0, "rgb": 1, "svideo": 2, "yuv": 3}
		iAVSwitch.setColorFormat(map[configElement.value])

	def setAspectRatio(configElement):
		map = {"4_3_letterbox": 0, "4_3_panscan": 1, "16_9": 2, "16_9_always": 3, "16_10_letterbox": 4, "16_10_panscan": 5, "16_9_letterbox": 6}
		iAVSwitch.setAspectRatio(map[configElement.value])

	def setSystem(configElement):
		map = {"pal": 0, "ntsc": 1, "multinorm": 2}
		iAVSwitch.setSystem(map[configElement.value])

	def setWSS(configElement):
		iAVSwitch.setAspectWSS()

	# this will call the "setup-val" initial
	config.av.colorformat.addNotifier(setColorFormat)
	config.av.aspectratio.addNotifier(setAspectRatio)
	config.av.tvsystem.addNotifier(setSystem)
	config.av.wss.addNotifier(setWSS)

	iAVSwitch.setInput("ENCODER") # init on startup
	if model in ("gb7356", "et5x00", "et6x00", "ixussone", "ixusszero", "axodin", "axase3", "optimussos1", "optimussos2", "gb800seplus", "gb800ueplus", "gbultrase", "gbultraue", "gbultraueh", "twinboxlcd"):
		detected = False
	else:
		detected = eAVSwitch.getInstance().haveScartSwitch()

	SystemInfo["ScartSwitch"] = detected

	def getProc(node):
		return procNode.get(node)

	# dictionary ... "proc_node_name" : _("human translatable texts"),
	procNode = {
		"ac3": _("AC3"),
		"center": _("center"),
		"dac": _("DAC"),
		"dts": _("DTS"),
		"downmix": _("Downmix"),
		"disabled": _("off"),
		"extrawide": _("extra wide"),
		"force_ac3": _("convert to AC3"),
		"force_ddp": _("force AC3+"),
		"force_dts": _("convert to DTS"),
		"hdmi": _("HDMI"),
		"hdmi_best": _("use best / controlled by HDMI"),
		"multichannel": _("convert to multi-channel PCM"),
		"none": _("off"),
		"off": _("Off"),
		"on": _("On"),
		"passthrough": _("Passthrough"),
		"spdif": _("SPDIF"),
		"use_hdmi_cacenter": _("use HDMI cacenter"),
		"use_hdmi_caps": _("Controlled by HDMI"),
		"wide": _("wide")
	}

	def readChoices(proc, choices, default):
		try:
			with open(proc, "r") as proc_stb_av:
				procChoices = proc_stb_av.read().strip()
		except:
			procChoices = ""
		if procChoices:
			choiceslist = procChoices.split(" ")
			choices = [(getProc(item)) for item in choiceslist]
			default = choiceslist[0]
		return (choices, default)

	if SystemInfo["CanDownmixAC3"]:
		def setAC3Downmix(configElement):
			open("/proc/stb/audio/ac3", "w").write(configElement.value)
		choices = [
			(getProc("downmix")),
			(getProc("passthrough"))
		]
		default = "downmix"
		if SystemInfo["DreamBoxAudio"]:
			choices = [
				(getProc("downmix")),
				(getProc("passthrough")),
				(getProc("multichannel")),
				(getProc("hdmi_best"))
			]
			config.av.downmix_ac3 = ConfigSelection(choices=choices, default=default)
		elif SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/ac3_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.downmix_ac3 = ConfigSelection(choices=choices, default=default)
		config.av.downmix_ac3.addNotifier(setAC3Downmix)

	if SystemInfo["CanAC3Transcode"]:
		def setAC3plusTranscode(configElement):
			open("/proc/stb/audio/ac3plus", "w").write(configElement.value)
		choices = [
			(getProc("use_hdmi_caps")),
			(getProc("force_ac3"))
		]
		default = "force_ac3"
		if SystemInfo["DreamBoxAudio"]:
			choices = [
				(getProc("use_hdmi_caps")),
				(getProc("force_ac3")),
				(getProc("multichannel")),
				(getProc("hdmi_best")),
				(getProc("force_ddp"))
			]
			config.av.transcodeac3plus = ConfigSelection(choices=choices, default=default)
		elif model in ("gb7252", "gb72604"):
			choices = [
				(getProc("downmix")),
				(getProc("passthrough")),
				(getProc("multichannel")),
				(getProc("force_ac3")),
				(getProc("force_dts"))
			]
			config.av.transcodeac3plus = ConfigSelection(choices=choices, default=default)
		elif SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/ac3plus_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.transcodeac3plus = ConfigSelection(choices=choices, default=default)
		config.av.transcodeac3plus.addNotifier(setAC3plusTranscode)

	if SystemInfo["CanDownmixDTS"]:
		def setDTSDownmix(configElement):
			open("/proc/stb/audio/dts", "w").write(configElement.value)
		choices = [
			(getProc("downmix")),
			(getProc("passthrough"))
		]
		default = "downmix"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/dts_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.downmix_dts = ConfigSelection(choices=choices, default=default)
		config.av.downmix_dts.addNotifier(setDTSDownmix)

	if SystemInfo["CanDTSHD"]:
		def setDTSHD(configElement):
			open("/proc/stb/audio/dtshd", "w").write(configElement.value)
		choices = [
			(getProc("downmix")),
			(getProc("force_dts")),
			(getProc("use_hdmi_caps")),
			(getProc("multichannel")),
			(getProc("hdmi_best"))
		]
		default = "downmix"
		if model in ("dm7080", "dm820"):
			choices = [
				(getProc("use_hdmi_caps")),
				(getProc("force_dts"))
			]
		elif SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/dtshd_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.dtshd = ConfigSelection(choices=choices, default=default)
		config.av.dtshd.addNotifier(setDTSHD)

	if SystemInfo["CanWMAPRO"]:
		def setWMAPRO(configElement):
			open("/proc/stb/audio/wmapro", "w").write(configElement.value)
		choices = [
			(getProc("downmix")),
			(getProc("passthrough")),
			(getProc("multichannel")),
			(getProc("hdmi_best"))
		]
		default = "downmix"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/wmapro_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.wmapro = ConfigSelection(choices=choices, default=default)
		config.av.wmapro.addNotifier(setWMAPRO)

	if SystemInfo["CanDownmixAAC"]:
		def setAACDownmix(configElement):
			open("/proc/stb/audio/aac", "w").write(configElement.value)
		choices = [
			(getProc("downmix")),
			(getProc("passthrough"))
		]
		default = "downmix"
		if SystemInfo["DreamBoxAudio"]:
			choices = [
				(getProc("downmix")),
				(getProc("passthrough")),
				(getProc("multichannel")),
				(getProc("hdmi_best"))
			]
		elif model in ("gb7252", "gb72604"):
			choices = [
				(getProc("downmix")),
				(getProc("passthrough")),
				(getProc("multichannel")),
				(getProc("force_ac3")),
				(getProc("force_dts")),
				(getProc("use_hdmi_cacenter")),
				(getProc("wide")),
				(getProc("extrawide"))
			]
		elif SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/aac_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.downmix_aac = ConfigSelection(choices=choices, default=default)
		config.av.downmix_aac.addNotifier(setAACDownmix)

	if SystemInfo["CanDownmixAACPlus"]:
		def setAACDownmixPlus(configElement):
			open("/proc/stb/audio/aacplus", "w").write(configElement.value)
		choices = [
			(getProc("downmix")),
			(getProc("passthrough")),
			(getProc("multichannel")),
			(getProc("force_ac3")),
			(getProc("force_dts")),
			(getProc("use_hdmi_cacenter")),
			(getProc("wide")),
			(getProc("extrawide"))
		]
		default = "downmix"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/aacplus_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.downmix_aacplus = ConfigSelection(choices=choices, default=default)
		config.av.downmix_aacplus.addNotifier(setAACDownmixPlus)

	if SystemInfo["CanAACTranscode"]:
		def setAACTranscode(configElement):
			open("/proc/stb/audio/aac_transcode", "w").write(configElement.value)
		choices = [
			(getProc("off")),
			(getProc("ac3")),
			(getProc("dts"))
		]
		default = "off"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/aac_transcode_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.transcodeaac = ConfigSelection(choices=choices, default=default)
		config.av.transcodeaac.addNotifier(setAACTranscode)

	if SystemInfo["CanBTAudio"]:
		def setBTAudio(configElement):
			open("/proc/stb/audio/btaudio", "w").write(configElement.value)
		choices = [
			(getProc("off")),
			(getProc("on"))
		]
		default = "off"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/btaudio_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.btaudio = ConfigSelection(choices=choices, default="off")
		config.av.btaudio.addNotifier(setBTAudio)

	if SystemInfo["CanBTAudioDelay"]:
		def setBTAudioDelay(configElement):
			try:
				with open("/proc/stb/audio/btaudio_delay", "w") as fd:
					fd.write(format(configElement.value * 90, "x"))
			except:
				SystemInfo["CanBTAudioDelay"] = False
		config.av.btaudiodelay = ConfigSelectionNumber(-1000, 1000, 5, default=0)
		config.av.btaudiodelay.addNotifier(setBTAudioDelay)

	if SystemInfo["CanChangeOsdAlpha"]:
		def setAlpha(config):
			print("[AVSwitch] Write to /proc/stb/video/alpha")
			open("/proc/stb/video/alpha", "w").write(str(config.value))
		config.av.osd_alpha = ConfigSlider(default=255, limits=(0, 255))
		config.av.osd_alpha.addNotifier(setAlpha)

	if SystemInfo["ScalerSharpness"]:
		def setScaler_sharpness(config):
			myval = int(config.value)
			try:
				print("--> setting scaler_sharpness to: %0.8X" % myval)
				print("[AVSwitch] Write to /proc/stb/vmpeg/0/pep_scaler_sharpness")
				open("/proc/stb/vmpeg/0/pep_scaler_sharpness", "w").write("%0.8X" % myval)
				print("[AVSwitch] Write to /proc/stb/vmpeg/0/pep_apply")
				open("/proc/stb/vmpeg/0/pep_apply", "w").write("1")
			except IOError:
				print("[AVSwitch] couldn't write pep_scaler_sharpness")

		if model == "gb7356":
			config.av.scaler_sharpness = ConfigSlider(default=5, limits=(0, 26))
		else:
			config.av.scaler_sharpness = ConfigSlider(default=13, limits=(0, 26))
		config.av.scaler_sharpness.addNotifier(setScaler_sharpness)
	else:
		config.av.scaler_sharpness = NoSave(ConfigNothing())

	if SystemInfo["CanPcmMultichannel"]:
		def setMultichannelPCM(configElement):
			print("[AVSwitch] Write to /proc/stb/audio/multichannel_pcm")
			open(SystemInfo["CanPcmMultichannel"], "w").write(configElement.value and "enable" or "disable")
		config.av.multichannel_pcm = ConfigYesNo(default=False)
		config.av.multichannel_pcm.addNotifier(setMultichannelPCM)

	if SystemInfo["CanAutoVolume"]:
		def setAutoVolume(configElement):
			open(SystemInfo["CanAutoVolume"], "w").write(configElement.value)
		choices = [
			(getProc("none")),
			(getProc("hdmi")),
			(getProc("spdif")),
			(getProc("dac"))
		]
		default = "none"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/avl_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.autovolume = ConfigSelection(choices=choices, default=default)
		config.av.autovolume.addNotifier(setAutoVolume)

	if SystemInfo["HasAutoVolumeLevel"]:
		def setAutoVolumeLevel(configElement):
			print("[AVSwitch] Write to /proc/stb/audio/autovolumelevel")
			open("/proc/stb/audio/autovolumelevel", "w").write(configElement.value and "enabled" or "disabled")
		config.av.autovolumelevel = ConfigYesNo(default=False)
		config.av.autovolumelevel.addNotifier(setAutoVolumeLevel)

	if SystemInfo["Can3DSurround"]:
		def set3DSurround(configElement):
			open(SystemInfo["Can3DSurround"], "w").write(configElement.value)
			choices = [
			(getProc("none")),
			(getProc("hdmi")),
			(getProc("spdif")),
			(getProc("dac"))
		]
		default = "none"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/3d_surround_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.surround_3d = ConfigSelection(choices=choices, default=default)
		config.av.surround_3d.addNotifier(set3DSurround)

	if SystemInfo["Can3DSpeaker"]:
		def set3DSpeaker(configElement):
			print("[AVSwitch] Write to /proc/stb/audio/3d_surround_speaker_position")
			open("/proc/stb/audio/3d_surround_speaker_position", "w").write(configElement.value)
		config.av.speaker_3d = ConfigSelection(default="disabled", choices=[("disabled", _("off")), ("center", _("center")), ("wide", _("wide")), ("extrawide", _("extra wide"))])
		config.av.speaker_3d.addNotifier(set3DSpeaker)

	if SystemInfo["Can3DSurroundSpeaker"]:
		def set3DSurroundSpeaker(configElement):
			open(SystemInfo["Can3DSurroundSpeaker"], "w").write(configElement.value)
		choices = [
			(getProc("disabled")),
			(getProc("center")),
			(getProc("wide")),
			(getProc("extrawide"))
		]
		default = "disabled"
		if SystemInfo["CanProc"]:
			proc = "/proc/stb/audio/3dsurround_choices"
			(choices, default) = readChoices(proc, choices, default)
		config.av.surround_3d_speaker = ConfigSelection(choices=choices, default=default)
		config.av.surround_3d_speaker.addNotifier(set3DSurroundSpeaker)

	if SystemInfo["Can3DSurroundSoftLimiter"]:
		def set3DSurroundSoftLimiter(configElement):
			print("[AVSwitch] Write to /proc/stb/audio/3dsurround_softlimiter")
			open("/proc/stb/audio/3dsurround_softlimiter", "w").write(configElement.value and "enabled" or "disabled")
		config.av.surround_softlimiter_3d = ConfigYesNo(default=False)
		config.av.surround_softlimiter_3d.addNotifier(set3DSurroundSoftLimiter)

	if SystemInfo["HDMIAudioSource"]:
		def setHDMIAudioSource(configElement):
			print("[AVSwitch] Write to /proc/stb/hdmi/audio_source")
			open(SystemInfo["HDMIAudioSource"], "w").write(configElement.value)
		config.av.hdmi_audio_source = ConfigSelection(default="pcm", choices=[("pcm", "PCM"), ("spdif", "SPDIF")])
		config.av.hdmi_audio_source.addNotifier(setHDMIAudioSource)

	def setVolumeStepsize(configElement):
		eDVBVolumecontrol.getInstance().setVolumeSteps(int(configElement.value))
	config.av.volume_stepsize = ConfigSelectionNumber(1, 10, 1, default=5)
	config.av.volume_stepsize.addNotifier(setVolumeStepsize)
