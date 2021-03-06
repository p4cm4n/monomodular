# http://aumhaa.blogspot.com

import Live
import time
import math

""" _Framework files """
from _Framework.ButtonElement import ButtonElement # Class representing a button a the controller
from _Framework.ButtonMatrixElement import ButtonMatrixElement # Class representing a 2-dimensional set of buttons
#from _Framework.ButtonSliderElement import ButtonSliderElement # Class representing a set of buttons used as a slider
from _Framework.ChannelStripComponent import ChannelStripComponent # Class attaching to the mixer of a given track
#from _Framework.ChannelTranslationSelector import ChannelTranslationSelector # Class switches modes by translating the given controls' message channel
#from _Framework.ClipSlotComponent import ClipSlotComponent # Class representing a ClipSlot within Live
from _Framework.CompoundComponent import CompoundComponent # Base class for classes encompasing other components to form complex components
from _Framework.ControlElement import ControlElement # Base class for all classes representing control elements on a controller 
from _Framework.ControlSurface import ControlSurface # Central base class for scripts based on the new Framework
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent # Base class for all classes encapsulating functions in Live
from _Framework.DeviceComponent import DeviceComponent # Class representing a device in Live
from _Framework.DisplayDataSource import DisplayDataSource # Data object that is fed with a specific string and notifies its observers
from _Framework.EncoderElement import EncoderElement # Class representing a continuous control on the controller
from _Framework.InputControlElement import * # Base class for all classes representing control elements on a controller
#from _Framework.LogicalDisplaySegment import LogicalDisplaySegment # Class representing a specific segment of a display on the controller
from _Framework.MixerComponent import MixerComponent # Class encompassing several channel strips to form a mixer
from _Framework.ModeSelectorComponent import ModeSelectorComponent # Class for switching between modes, handle several functions with few controls
from _Framework.NotifyingControlElement import NotifyingControlElement # Class representing control elements that can send values
from _Framework.PhysicalDisplayElement import PhysicalDisplayElement # Class representing a display on the controller
from _Framework.SceneComponent import SceneComponent # Class representing a scene in Live
from _Framework.SessionComponent import SessionComponent # Class encompassing several scene to cover a defined section of Live's session
from _Framework.SessionZoomingComponent import SessionZoomingComponent # Class using a matrix of buttons to choose blocks of clips in the session
from _Framework.SliderElement import SliderElement # Class representing a slider on the controller
from _Framework.TrackEQComponent import TrackEQComponent # Class representing a track's EQ, it attaches to the last EQ device in the track
from _Framework.TrackFilterComponent import TrackFilterComponent # Class representing a track's filter, attaches to the last filter in the track
from _Framework.TransportComponent import TransportComponent # Class encapsulating all functions in Live's transport section

"""Custom files, overrides, and files from other scripts"""
from ShiftModeComponent import ShiftModeComponent
from FunctionModeComponent import FunctionModeComponent
from OSCFlashingButtonElement import OSCFlashingButtonElement
from MonoEncoderElement2 import MonoEncoderElement2
from DeviceSelectorComponent import DeviceSelectorComponent
from DetailViewControllerComponent import DetailViewControllerComponent
from ResetSendsComponent import ResetSendsComponent
from MonoBridgeElement import MonoBridgeElement
from MonomodComponent import MonomodComponent
from MonomodModeComponent import MonomodModeComponent
from SpecialMonomodComponent import SpecialMonomodComponent
from NameServerSessionComponent import NameServerSessionComponent
from NameServerSceneComponent import NameServerSceneComponent
from NameServerClipSlotComponent import NameServerClipSlotComponent



#this bit of code replaces the default path where Python assumes the _Framework file resides, therefore the 
#override file has to be carefully written to make sure it doesn't interfere with other scripts that us it, 
#since this path will be used for the remainder of the Python session (i.e. until Live quits and restarts)
#import sys
#sys.modules['ClipSlotComponent'] = sys.modules['AumPad.NewClipSlotComponent']

import LiveUtils
from _Generic.Devices import *
from AumPad_Map import *

""" Here we define some global variables """
CHANNEL = 0 
session = None 
mixer = None 
session2 = None
mixer2 = None


class AumPad(ControlSurface):
	__module__ = __name__
	__doc__ = " MonOhmod companion controller script "


	def __init__(self, c_instance):
		"""everything except the '_on_selected_track_changed' override and 'disconnect' runs from here"""
		ControlSurface.__init__(self, c_instance)
		self.log_message("--------------= AumPad log opened =--------------") 
		self._suggested_input_port = 'None'
		self._suggested_output_port = 'None'
		self.set_suppress_rebuild_requests(True)
		self._monomod_version = 'b994'
		self._host_name = 'AumPad'
		self._color_type = 'AumPad'
		self._update_linked_device_selection = None
		self.connected = 0
		self.hosts = []
		self._osc_registry = {}
		self._bright = True
		self._display_button_names = DISPLAY_BUTTON_NAMES
		self._rgb = 0
		self._timer = 0
		self.flash_status = 1
		self._is_split = True
		self._clutch_device_selection = False
		self._backlight = 127
		self._backlight_type = 'static'
		self._ohm = 127
		self._ohm_type = 'static'
		self._pad_translations = PAD_TRANSLATION
		self._mem = [4, 8, 12]
		self._mixers = []
		self._sessions = []
		self._zooms = []
		self._function_modes = []
		self._setup_monobridge()
		self._setup_controls()
		self._setup_transport_control() 
		self._setup_mixer_control()
		self._setup_session_control()
		self._setup_device_control()
		self._setup_crossfader()
		self._setup_device_selector()
		self._setup_monomod()
		self._setup_modes() 
		self._setup_touchosc()
		self.set_suppress_rebuild_requests(False)
		self.song().view.add_selected_track_listener(self._update_selected_device)
		#self.reset()
		#self.refresh_state()
		self.show_message('AumPad Control Surface Loaded')
	

	"""script initialization methods"""
	def _setup_monobridge(self):
		self._monobridge = MonoBridgeElement(self)
		self._monobridge.name = 'MonoBridge'
	

	def _setup_controls(self):
		is_momentary = True
		self._fader = [None for index in range(8)]
		self._dial = [None for index in range(16)]
		self._button = [None for index in range(8)]
		self._menu = [None for index in range(6)]
		for index in range(8):
			self._fader[index] = MonoEncoderElement2(MIDI_CC_TYPE, CHANNEL, OHM_FADERS[index], Live.MidiMap.MapMode.absolute, 'Fader_' + str(index), index, '/2/fader/'+str(index),	 '/2/v_fader/'+str(index), '/2/strip_'+str(index), self)
		for index in range(8):
			self._button[index] = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, OHM_BUTTONS[index], 'Button_'+str(index), '/2/p_button/'+str(index), '/2/c_button/'+str(index),  None, self)
		for index in range(16):
			self._dial[index] = MonoEncoderElement2(MIDI_CC_TYPE, CHANNEL, OHM_DIALS[index], Live.MidiMap.MapMode.absolute, 'Dial_' + str(index), index + 8, '/2/dial/'+str(index), '/2/lk_'+str(index), '/2/lk_'+str(index + 16), self)
		for index in range(6):
			self._menu[index] = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, OHM_MENU[index], 'Menu_' + str(index), '/2/p_menu/'+str(index), '/2/c_menu/'+str(index), '/2/n_menu/'+str(index), self)	
		self._crossfader = MonoEncoderElement2(MIDI_CC_TYPE, CHANNEL, CROSSFADER, Live.MidiMap.MapMode.absolute, "Crossfader", 24, '/2/xfader', None, None, self)
		self._livid = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, LIVID, 'Livid_Button', '/2/p_livid', '/2/c_livid', None, self)
		self._shift_l = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, SHIFT_L, 'Shift_Button_Left', '/2/p_shift_l', '/2/c_shift_l', None, self)
		self._shift_r = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, SHIFT_R, 'Shift_Button_Right', '/2/p_shift_r', '/2/c_shift_r', None, self)
		self._matrix = ButtonMatrixElement()
		self._matrix.name = 'Matrix'
		self._monomod = ButtonMatrixElement()
		self._monomod.name = 'Monomod'
		self._grid = [None for index in range(8)]
		for column in range(8):
			self._grid[column] = [None for index in range(8)]
			for row in range(8):
				self._grid[column][row] = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, (column * 8) + row, 'Grid_' + str(column) + '_' + str(row), '/2/p_grid/'+str(column)+'/'+str(row), '/2/c_grid/'+str(column)+'/'+str(row), '/2/n_grid/'+str(column)+'/'+str(row), self)
		for row in range(5):
			button_row = []
			for column in range(7):
				button_row.append(self._grid[column][row])
			self._matrix.add_row(tuple(button_row)) 
		for row in range(8):
			button_row = []
			for column in range(8):
				button_row.append(self._grid[column][row])
			self._monomod.add_row(tuple(button_row))
		self._dummy_button = ButtonElement(is_momentary, MIDI_NOTE_TYPE, 15, -1)
		self._dummy_button.name = 'Dummy1'
		self._dummy_button2 = ButtonElement(is_momentary, MIDI_NOTE_TYPE, 15, -1)
		self._dummy_button2.name = 'Dummy2'
		self._dummy_button3 = ButtonElement(is_momentary, MIDI_NOTE_TYPE, 15, -1)
		self._dummy_button2.name = 'Dummy3'
		self._monomod256 = ButtonMatrixElement()
		self._monomod256.name = 'Monomod256'
		self._square = [None for index in range(16)]
		for column in range(16):
			self._square[column] = [None for index in range(16)]
			for row in range(16):
				self._square[column][row] = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, int(column/8) + 1, row + ((column%8) * 16), '256Grid_' + str(column) + '_' + str(row), '/1/p_grid/'+str(column)+'/'+str(row), '/1/c_grid/'+str(column)+'/'+str(row), None, self)
				#self._square[column][row] = FlashingButtonElement(is_momentary, 0, 15, -1, '256Grid_' + str(column) + '_' + str(row), '/1/p_grid/'+str(column)+'/'+str(row), '/1/c_grid/'+str(column)+'/'+str(row), self)
		for row in range(16):
			button_row = []
			for column in range(16):
				button_row.append(self._square[column][row])
			self._monomod256.add_row(tuple(button_row))
		self._bank_buttons = ButtonMatrixElement()
		self._key_buttons = ButtonMatrixElement()
		self._bank_button = [None for index in range(8)]
		for index in range(8):
			self._bank_button[index] = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, 15, index, '256Grid_Bank_' + str(index), '/1/p_a/'+str(index), '/1/c_a/'+str(index), None, self)
		button_row = []
		for index in range(8):
			button_row.append(self._bank_button[index])
		self._bank_buttons.add_row(tuple(button_row))
		button_row = []
		self._key_button = [None for index in range(8)]
		for index in range(8):
			self._key_button[index] = OSCFlashingButtonElement(is_momentary, MIDI_NOTE_TYPE, 15, index+8, '256Grid_Key_' + str(index), '/1/p_s/'+str(index), '/1/c_s/'+str(index), None, self)
		for index in range(8):
			button_row.append(self._key_button[index])
		self._key_buttons.add_row(tuple(button_row))
	

	def _setup_transport_control(self):
		self._transport = TransportComponent() 
		self._transport.name = 'Transport'
	

	def _setup_mixer_control(self):
		is_momentary = True
		self._num_tracks = (4) #A mixer is one-dimensional; 
		global mixer
		mixer = MixerComponent(8, 0, False, True)
		mixer.name = 'Left_Mixer'
		self._mixer = mixer
		mixer.set_track_offset(0) #Sets start point for mixer strip (offset from left)
		for index in range(4):
			mixer.channel_strip(index).set_volume_control(self._fader[index])
		for index in range(8):
			mixer.channel_strip(index)._on_cf_assign_changed = self.mixer_on_cf_assign_changed(mixer.channel_strip(index))
			mixer.channel_strip(index).name = 'Mixer_ChannelStrip_' + str(index)
			mixer.track_filter(index).name = 'Mixer_TrackFilter_' + str(index)
			mixer.channel_strip(index)._invert_mute_feedback = True
		self.song().view.selected_track = mixer.channel_strip(0)._track #set the selected strip to the first track, so that we don't, for example, try to assign a button to arm the master track, which would cause an assertion error
		global mixer2
		mixer2 = MixerComponent(4, 4, False, False)
		mixer2.name = 'Right_Mixer'
		self._mixer2 = mixer2
		mixer2.set_track_offset(4)
		for index in range(4):
			mixer2.channel_strip(index)._on_cf_assign_changed = self.mixer_on_cf_assign_changed(mixer2.channel_strip(index))
			mixer2.channel_strip(index).name = 'Mixer2_ChannelStrip_' + str(index)
			mixer2.return_strip(index)._on_cf_assign_changed = self.mixer_on_cf_assign_changed(mixer2.return_strip(index))
			mixer2.return_strip(index).name = 'Mixer2_ReturnStrip_' + str(index)
			mixer2.channel_strip(index).set_volume_control(self._fader[index + 4]) 
			mixer2.channel_strip(index)._invert_mute_feedback = True
			mixer2.return_strip(index)._invert_mute_feedback = True
		self._mixers = [self._mixer, self._mixer2]
		self._send_reset = ResetSendsComponent(self)
		self._send_reset.name = 'Sends_Reset'
		self._mixer._reassign_tracks()
		self._mixer2._reassign_tracks()
	

	def _setup_session_control(self):
		is_momentary = True
		num_tracks = 4
		num_scenes = 5 
		global session
		session = NameServerSessionComponent(num_tracks, num_scenes, self)
		session.name = "Left_Session"
		session.set_offsets(0, 0)
		self._session = session		 
		self._session.set_stop_track_clip_value(STOP_CLIP[self._rgb])
		self._scene = [None for index in range(5)]
		for row in range(num_scenes):
			self._scene[row] = session.scene(row)
			self._scene[row].name = 'L_Scene_' + str(row)
			for column in range(num_tracks):
				clip_slot = self._scene[row].clip_slot(column)
				clip_slot.name = str(column) + '_Clip_Slot_L_' + str(row)
				clip_slot.set_triggered_to_play_value(CLIP_TRG_PLAY[self._rgb])
				clip_slot.set_triggered_to_record_value(CLIP_TRG_REC[self._rgb])
				clip_slot.set_stopped_value(CLIP_STOP[self._rgb])
				clip_slot.set_started_value(CLIP_STARTED[self._rgb])
				clip_slot.set_recording_value(CLIP_RECORDING[self._rgb])
		session.set_mixer(mixer)
		self._session_zoom = SessionZoomingComponent(session)	 
		self._session_zoom.name = 'L_Session_Overview'
		self._session_zoom.set_stopped_value(ZOOM_STOPPED[self._rgb])
		self._session_zoom.set_playing_value(ZOOM_PLAYING[self._rgb])
		self._session_zoom.set_selected_value(ZOOM_SELECTED[self._rgb])
		self._session_zoom._zoom_button = (self._dummy_button)
		self._session_zoom.set_enabled(True) 
		global session2
		session2 = NameServerSessionComponent(num_tracks, num_scenes, self)
		session2.name = 'Right_Session'
		session2.set_offsets(4, 0)
		self._session2 = session2
		self._session2.set_stop_track_clip_value(STOP_CLIP[self._rgb])
		self._scene2 = [None for index in range(5)]
		for row in range(num_scenes):
			self._scene2[row] = session2.scene(row)
			self._scene2[row].name = 'R_Scene_' + str(row)
			for column in range(num_tracks):
				clip_slot = self._scene2[row].clip_slot(column)
				clip_slot.name = str(column) + '_Clip_Slot_R_' + str(row)
				clip_slot.set_triggered_to_play_value(CLIP_TRG_PLAY[self._rgb])
				clip_slot.set_triggered_to_record_value(CLIP_TRG_REC[self._rgb])
				clip_slot.set_stopped_value(CLIP_STOP[self._rgb])
				clip_slot.set_started_value(CLIP_STARTED[self._rgb])
				clip_slot.set_recording_value(CLIP_RECORDING[self._rgb])
		session2.set_mixer(self._mixer2)
		self._session2.add_offset_listener(self._on_session_offset_changes)
		self._session_zoom2 = SessionZoomingComponent(session2)	   
		self._session_zoom2.name = 'R_Session_Overview'
		self._session_zoom2.set_stopped_value(ZOOM_STOPPED[self._rgb])
		self._session_zoom2.set_playing_value(ZOOM_PLAYING[self._rgb])
		self._session_zoom2.set_selected_value(ZOOM_SELECTED[self._rgb])
		self._session_zoom.set_enabled(True) 
		self._session_zoom2._zoom_button = (self._dummy_button2)
		self._session_main = NameServerSessionComponent(8, num_scenes, self)
		self._session_main.name = 'Main_Session'
		self._session_main.set_stop_track_clip_value(STOP_CLIP[self._rgb])
		self._scene_main = [None for index in range(5)]
		for row in range(num_scenes):
			self._scene_main[row] = self._session_main.scene(row)
			self._scene_main[row].name = 'M_Scene_' + str(row)
			for column in range(8):
				clip_slot = self._scene_main[row].clip_slot(column)
				clip_slot.name = str(column) + '_Clip_Slot_M_' + str(row)
				clip_slot.set_triggered_to_play_value(CLIP_TRG_PLAY[self._rgb])
				clip_slot.set_triggered_to_record_value(CLIP_TRG_REC[self._rgb])
				clip_slot.set_stopped_value(CLIP_STOP[self._rgb])
				clip_slot.set_started_value(CLIP_STARTED[self._rgb])
				clip_slot.set_recording_value(CLIP_RECORDING[self._rgb])
		self._session_main.set_mixer(self._mixer)
		self._session_zoom_main = SessionZoomingComponent(self._session_main)
		self._session_zoom_main.name = 'M_Session_Overview'
		self._session_zoom_main.set_stopped_value(ZOOM_STOPPED[self._rgb])
		self._session_zoom_main.set_playing_value(ZOOM_PLAYING[self._rgb])
		self._session_zoom_main.set_selected_value(ZOOM_SELECTED[self._rgb])
		self._session_zoom_main.set_enabled(True)
		self._session_zoom_main._zoom_button = (self._dummy_button3)
		self._sessions = [self._session, self._session2, self._session_main]
		self._zooms = [self._session_zoom, self._session_zoom2, self._session_zoom_main]
	

	def _assign_session_colors(self):
		num_tracks = 4
		num_scenes = 5 
		self._session.set_stop_track_clip_value(STOP_ALL[self._rgb])
		self._session2.set_stop_track_clip_value(STOP_ALL[self._rgb])
		self._session_main.set_stop_track_clip_value(STOP_ALL[self._rgb])
		for row in range(num_scenes): 
			for column in range(num_tracks):
				self._scene[row].clip_slot(column).set_triggered_to_play_value(CLIP_TRG_PLAY[self._rgb])
				self._scene[row].clip_slot(column).set_triggered_to_record_value(CLIP_TRG_REC[self._rgb])
				self._scene[row].clip_slot(column).set_stopped_value(CLIP_STOP[self._rgb])
				self._scene[row].clip_slot(column).set_started_value(CLIP_STARTED[self._rgb])
				self._scene[row].clip_slot(column).set_recording_value(CLIP_RECORDING[self._rgb])	
				self._scene2[row].clip_slot(column).set_triggered_to_play_value(CLIP_TRG_PLAY[self._rgb])
				self._scene2[row].clip_slot(column).set_triggered_to_record_value(CLIP_TRG_REC[self._rgb])
				self._scene2[row].clip_slot(column).set_stopped_value(CLIP_STOP[self._rgb])
				self._scene2[row].clip_slot(column).set_started_value(CLIP_STARTED[self._rgb])
				self._scene2[row].clip_slot(column).set_recording_value(CLIP_RECORDING[self._rgb])	
		for row in range(num_scenes): 
			for column in range(8):
				self._scene_main[row].clip_slot(column).set_triggered_to_play_value(CLIP_TRG_PLAY[self._rgb])
				self._scene_main[row].clip_slot(column).set_triggered_to_record_value(CLIP_TRG_REC[self._rgb])
				self._scene_main[row].clip_slot(column).set_stopped_value(CLIP_STOP[self._rgb])
				self._scene_main[row].clip_slot(column).set_started_value(CLIP_STARTED[self._rgb])
				self._scene_main[row].clip_slot(column).set_recording_value(CLIP_RECORDING[self._rgb])		
		self._session_zoom.set_stopped_value(ZOOM_STOPPED[self._rgb])
		self._session_zoom.set_playing_value(ZOOM_PLAYING[self._rgb])
		self._session_zoom.set_selected_value(ZOOM_SELECTED[self._rgb])
		self._session_zoom2.set_stopped_value(ZOOM_STOPPED[self._rgb])
		self._session_zoom2.set_playing_value(ZOOM_PLAYING[self._rgb])
		self._session_zoom2.set_selected_value(ZOOM_SELECTED[self._rgb])
		self._session_zoom_main.set_stopped_value(ZOOM_STOPPED[self._rgb])
		self._session_zoom_main.set_playing_value(ZOOM_PLAYING[self._rgb])
		self._session_zoom_main.set_selected_value(ZOOM_SELECTED[self._rgb])
		self.refresh_state()
	

	def _setup_device_control(self):
		self._device = DeviceComponent()
		self._device.name = 'Device_Component'
		self._device.set_device = self.device_set_device(self._device)
		self._device._is_banking_enabled = self.device_is_banking_enabled(self._device)
		self.set_device_component(self._device)
		#self.bank = DeviceCallbackComponent(self._device, 1)
		#self.bank.name = 'Device_Bank'
		#self.device_instance = DeviceCallbackComponent(self._device, 2)
		#self.device_instance.name = 'Device_Instance'
		self._device_navigator = DetailViewControllerComponent()
		self._device_navigator.name = 'Device_Navigator'
		self._device_selection_follows_track_selection = FOLLOW
	

	def _setup_crossfader(self):
		self._mixer.set_crossfader_control(self._crossfader)
	

	def _setup_device_selector(self):
		self._device_selector = DeviceSelectorComponent(self)
		self._device_selector.name = 'Device_Selector'
	

	def _setup_monomod(self):
		self._host = MonomodComponent(self)
		self._host.name = 'Monomod_Host'
		self._host2 = SpecialMonomodComponent(self)
		self._host2.name = '256_Monomod_Host'
		self.hosts = [self._host, self._host2]
	

	def _setup_modes(self):
		self._monomod_mode = MonomodModeComponent(self)
		self._monomod_mode.name = 'Monomod_Mode'
		self._monomod_mode.set_mode_toggle(self._livid)
		self._shift_mode = ShiftModeComponent(self, self.shift_update) 
		self._shift_mode.name = 'Shift_Mode'
		self._shift_mode.set_mode_toggle(self._shift_l, self._shift_r)
		self._l_function_mode = FunctionModeComponent(self, self.l_function_update)
		self._l_function_mode.name = 'Left_Function_Mode'
		self._r_function_mode = FunctionModeComponent(self, self.r_function_update)
		self._r_function_mode.name = 'Right_Function_Mode'
		self._m_function_mode = FunctionModeComponent(self, self.m_function_update)
		self._m_function_mode.name = 'Main_Function_Mode'
		self._function_modes = [self._l_function_mode, self._r_function_mode, self._m_function_mode]
	

	def _setup_touchosc(self):
		self._osc_registry = {}
		self._osc_registry['/ping'] = self._monobridge.ping
		self._osc_registry['/1'] = self._monobridge.page1
		self._osc_registry['/2'] = self._monobridge.page2
		for control in self.controls:
			if hasattr(control, 'osc'):
				self._osc_registry[control.osc] = control.set_value
			if hasattr(control, 'osc_alt'):
				self._osc_registry[control.osc_alt] = control.set_value
				#self.log_message('create dict key: ' + str(control.osc) + str(control.name))
	


	"""shift/zoom methods"""
	def deassign_matrix(self):
		for session in self._sessions:
			session.set_stop_track_clip_buttons(None)
			session.set_track_bank_buttons(None, None)
			session.set_scene_bank_buttons(None, None)
		for zoom in self._zooms:
			zoom.set_button_matrix(None)
			zoom.set_nav_buttons(None, None, None, None)
		for column in range(4):
			self._mixer2.channel_strip(column).set_select_button(None)
			self._mixer2.return_strip(column).set_mute_button(None)
			self._mixer2.return_strip(column).set_solo_button(None)
			self._mixer2.return_strip(column).set_arm_button(None)
			self._mixer2.return_strip(column).set_crossfade_toggle(None)
			self._mixer2.return_strip(column).set_select_button(None)			#shouldn't this be somewhere else?
			self._mixer2.channel_strip(column).set_crossfade_toggle(None)
			self._mixer2.channel_strip(column).set_mute_button(None)
			self._mixer2.channel_strip(column).set_solo_button(None)
			self._mixer2.channel_strip(column).set_arm_button(None)
			for row in range(5):
				self._scene[row].clip_slot(column).set_launch_button(None)
				self._scene2[row].clip_slot(column).set_launch_button(None)
		for index in range(5):
			self._scene[index].set_launch_button(None)
			self._scene2[index].set_launch_button(None)
			self._scene_main[index].set_launch_button(None)
		for column in range(8):
			self._button[column].set_on_off_values(127, 0)
			self._mixer.channel_strip(column).set_select_button(None)
			self._mixer.channel_strip(column).set_crossfade_toggle(None)
			self._mixer.channel_strip(column).set_mute_button(None)
			self._mixer.channel_strip(column).set_solo_button(None)
			self._mixer.channel_strip(column).set_arm_button(None)
			for row in range(5):
				self._scene_main[row].clip_slot(column).set_launch_button(None)
			for row in range(8):
				self._grid[column][row].set_channel(0)
				self._grid[column][row].release_parameter()
				self._grid[column][row].use_default_message()
				self._grid[column][row].set_enabled(True)
				self._grid[column][row].set_on_off_values(127, 0)
				self._grid[column][row].send_value(0, True)
		self._send_reset.set_buttons(tuple(None for index in range(4)))
	

	def zoom_off(self):
		for column in range(4):
			self._grid[column][5].set_on_value(MUTE[self._rgb])
			self._mixer.channel_strip(column).set_mute_button(self._grid[column][5])
			self._grid[column][6].set_on_value(SOLO[self._rgb])
			self._mixer.channel_strip(column).set_solo_button(self._grid[column][6])
			self._grid[column][7].set_on_value(ARM[self._rgb])
			self._mixer.channel_strip(column).set_arm_button(self._grid[column][7])
			for row in range(5):
				self._scene[row].clip_slot(column).set_launch_button(self._grid[column][row])
			if(self._r_function_mode._mode_index in range(0,3)):
				self._grid[column + 4][5].set_on_value(MUTE[self._rgb])
				self._mixer2.channel_strip(column).set_mute_button(self._grid[column + 4][5])
				self._grid[column + 4][6].set_on_value(SOLO[self._rgb])
				self._mixer2.channel_strip(column).set_solo_button(self._grid[column + 4][6])
				self._grid[column + 4][7].set_on_value(ARM[self._rgb])
				self._mixer2.channel_strip(column).set_arm_button(self._grid[column + 4][7])
				for row in range(5):
					self._scene2[row].clip_slot(column).set_launch_button(self._grid[column + 4][row])
			elif(self._r_function_mode._mode_index is 3):
				self._grid[column + 4][5].set_on_value(MUTE[self._rgb])
				self._mixer2.return_strip(column).set_mute_button(self._grid[column + 4][5])
				self._grid[column + 4][6].set_on_value(SOLO[self._rgb])
				self._mixer2.return_strip(column).set_solo_button(self._grid[column + 4][6])
				#self._mixer2.return_strip(column).set_crossfade_toggle(self._grid[column + 4][7])
				for row in range(5):
					self._grid[column + 4][row].send_value(USER1_COLOR[self._rgb], True)
					self._grid[column + 4][row].set_channel(RIGHT_USER1_CHANNEL)
					self._grid[column + 4][row].set_identifier(RIGHT_USER1_MAP[column][row])
					self._grid[column + 4][row].set_enabled(False)	 #this has to happen for translate to work
					self._monobridge._send('remap', self._grid[column + 4][row].osc_name)
		if(self._r_function_mode._mode_index is 0):
			for index in range(4):
				self._grid[index + 4][7].send_value(SEND_RESET[self._rgb], True)
			self._send_reset.set_buttons(tuple(self._grid[index + 4][7] for index in range(4)))
	

	def zoom_off_m(self):
		self.deassign_right_controls()
		for column in range(8):
			self._grid[column][5].set_on_value(MUTE[self._rgb])
			self._mixer.channel_strip(column).set_mute_button(self._grid[column][5])
			self._grid[column][6].set_on_value(SOLO[self._rgb])
			self._mixer.channel_strip(column).set_solo_button(self._grid[column][6])
			self._grid[column][7].set_on_value(ARM[self._rgb])
			self._mixer.channel_strip(column).set_arm_button(self._grid[column][7])
			for row in range(5):
				self._scene_main[row].clip_slot(column).set_launch_button(self._grid[column][row])

	

	def zoom_left(self):
		track_stop_buttons = []
		track_stop_buttons2 = []
		for index in range(4):
			self._grid[index][6].set_on_value(CROSSFADE_TOGGLE[self._rgb])
			self._mixer.channel_strip(index).set_crossfade_toggle(self._grid[index][6])
			self._grid[index + 4][6].set_on_value(CROSSFADE_TOGGLE[self._rgb])
			self._mixer2.channel_strip(index).set_crossfade_toggle(self._grid[index + 4][6])
			self._grid[index][7].set_on_value(TRACK_STOP[self._rgb])
			track_stop_buttons.append(self._grid[index][7])
			self._grid[index + 4][7].set_on_value(TRACK_STOP[self._rgb])
			track_stop_buttons2.append(self._grid[index + 4][7])
		for index in range(5):
			self._grid[7][index].set_off_value(SCENE_LAUNCH[self._rgb])
			self._scene[index].set_launch_button(self._grid[7][index])
		self._session.set_stop_track_clip_buttons(tuple(track_stop_buttons))
		self._session2.set_stop_track_clip_buttons(tuple(track_stop_buttons2))
		self._session_zoom.set_button_matrix(self._matrix)
		self._grid[0][5].set_on_value(RECORD[self._rgb])
		self._transport.set_record_button(self._grid[0][5])
		self._grid[1][5].set_on_value(OVERDUB[self._rgb])
		self._transport.set_overdub_button(self._grid[1][5])
		self._grid[2][5].set_on_value(LOOP[self._rgb])
		self._transport.set_loop_button(self._grid[2][5])
		self._grid[3][5].set_on_value(STOP_ALL[self._rgb])	
		session.set_stop_all_clips_button(self._grid[3][5])
		for index in range(4):
			self._grid[index + 4][5].send_value(SEND_RESET[self._rgb], True)
		self._send_reset.set_buttons(tuple(self._grid[index + 4][5] for index in range(4)))
		for index in range(4):
			self._button[index + 4].set_off_value(DEVICE_SELECT[self._rgb])
		self._device_selector.assign_buttons(tuple(self._button[index + 4] for index in range(4)), 4)
	
	
	def zoom_right(self):
		track_stop_buttons = []
		track_stop_buttons2 = []
		for index in range(4):
			self._grid[index][6].set_on_value(CROSSFADE_TOGGLE[self._rgb])
			self._mixer.channel_strip(index).set_crossfade_toggle(self._grid[index][6])
			self._grid[index][7].set_off_value(TRACK_STOP[self._rgb])
			track_stop_buttons.append(self._grid[index][7])
		for index in range(5):
			self._grid[7][index].set_off_value(SCENE_LAUNCH[self._rgb])
			self._scene2[index].set_launch_button(self._grid[7][index])
		self._session.set_stop_track_clip_buttons(tuple(track_stop_buttons))
		if(self._r_function_mode._mode_index < 3):
			for index in range(4):
				self._grid[index + 4][6].set_on_value(CROSSFADE_TOGGLE[self._rgb])
				self._mixer2.channel_strip(index).set_crossfade_toggle(self._grid[index + 4][6])
				self._grid[index + 4][7].set_off_value(TRACK_STOP[self._rgb])
				track_stop_buttons2.append(self._grid[index + 4][7])
			self._session2.set_stop_track_clip_buttons(tuple(track_stop_buttons2))
		else:
			for index in range(4):
				self._grid[index + 4][6].set_on_value(CROSSFADE_TOGGLE[self._rgb])
				self._mixer2.return_strip(index).set_crossfade_toggle(self._grid[index + 4][6])
		self._session_zoom2.set_button_matrix(self._matrix)
		self._grid[0][5].set_on_value(RECORD[self._rgb])
		self._transport.set_record_button(self._grid[0][5])
		self._grid[1][5].set_on_value(OVERDUB[self._rgb])
		self._transport.set_overdub_button(self._grid[1][5])
		self._grid[2][5].set_on_value(LOOP[self._rgb])
		self._transport.set_loop_button(self._grid[2][5])
		self._grid[3][5].set_on_value(STOP_ALL[self._rgb])
		session.set_stop_all_clips_button(self._grid[3][5])
		for index in range(4):
			self._grid[index + 4][5].send_value(SEND_RESET[self._rgb], True)
		self._send_reset.set_buttons(tuple(self._grid[index + 4][5] for index in range(4)))
		for index in range(4):
			self._button[index]._off_value = DEVICE_SELECT[self._rgb]
		self._device_selector.assign_buttons(tuple(self._button[index] for index in range(4)), 0)

	

	def zoom_main(self):
		track_stop_buttons = []
		for index in range(8):
			self._grid[index][6].set_on_value(CROSSFADE_TOGGLE[self._rgb])
			self._mixer.channel_strip(index).set_crossfade_toggle(self._grid[index][6])
			self._grid[index][7].set_on_value(TRACK_STOP[self._rgb])
			track_stop_buttons.append(self._grid[index][7])
		for index in range(5):
			self._grid[7][index].set_on_value(SCENE_LAUNCH[self._rgb])
			self._scene_main[index].set_launch_button(self._grid[7][index])
		self._session_main.set_stop_track_clip_buttons(tuple(track_stop_buttons))
		self._session_zoom_main.set_button_matrix(self._matrix)
		self._grid[0][5].set_on_value(RECORD[self._rgb])
		self._transport.set_record_button(self._grid[0][5])
		self._grid[1][5].set_on_value(OVERDUB[self._rgb])
		self._transport.set_overdub_button(self._grid[1][5])
		self._grid[2][5].set_on_value(LOOP[self._rgb])
		self._transport.set_loop_button(self._grid[2][5])
		self._grid[3][5].set_on_value(STOP_ALL[self._rgb])	
		session.set_stop_all_clips_button(self._grid[3][5])
		for index in range(4):
			self._grid[index + 4][5].send_value(SEND_RESET[self._rgb], True)
		self._send_reset.set_buttons(tuple(self._grid[index + 4][5] for index in range(4)))
		for index in range(4):
			self._button[index + 4].set_off_value(DEVICE_SELECT[self._rgb])
		self._device_selector.assign_buttons(tuple(self._button[index + 4] for index in range(4)), 4)

	


	"""function mode callbacks"""
	def l_function_update(self):
		#self.log_message('l_function_update ' + str(self._l_function_mode._mode_index))
		mode = self._l_function_mode._mode_index
		if(self._l_function_mode.is_enabled() is False):
			self._l_function_mode.set_mode_buttons(None)
		elif(self._l_function_mode.is_enabled() is True):
			if(len(self._l_function_mode._modes_buttons) is 0):
				for index in range(4):
					self._mixer.channel_strip(index).set_select_button(None)
				buttons = []
				for index in range(4):
					buttons.append(self._button[index]) 
				self._l_function_mode.set_mode_buttons(tuple(buttons))
			if(self._shift_mode._mode_index is 2):
				for index in range(4):
					if(mode != index):
						self._button[index].turn_off()
					else:
						self._button[index].turn_on()
		if(mode is 0):
			self.assign_left_device_dials()
			self.show_message('Mixer Split:Left Side Dials in Device(Top) and Selected Send(Bottom) Mode')
		elif(mode is 1):
			self.assign_left_send_dials()
			self.show_message('Mixer Split:Left Side Dials in Channel Send Mode (Sends 1-3)')
		elif(mode is 2):
			self.assign_left_filter_dials()
			self.show_message('Mixer Split:Left Side Dials in Filter(Top) and Pan(Bottom) Mode')
		elif(mode is 3):
			self.assign_left_user_dials()
			self.show_message('Mixer Split:Left Side Dials in User Map Mode')
	

	def r_function_update(self):
		#self.log_message('r_function_update '+ str(self._r_function_mode._mode_index))
		mode = self._r_function_mode._mode_index
		if(self._r_function_mode.is_enabled() is False):
			self._r_function_mode.set_mode_buttons(None)
			self._session2.set_show_highlight(False)
			self._session._highlighting_callback(self._session._track_offset, self._session._scene_offset, 4, 5, 1)
		elif(self._r_function_mode.is_enabled() is True):
			if(len(self._r_function_mode._modes_buttons) is 0):
				for index in range(4):
					self._mixer2.channel_strip(index).set_select_button(None)
				buttons = []
				for index in range(4):
					buttons.append(self._button[index + 4]) 
				self._r_function_mode.set_mode_buttons(tuple(buttons))
			if(self._shift_mode._mode_index is 3):
				for index in range(4):
					if(mode != index):
						self._button[index + 4].turn_off()
					else:
						self._button[index + 4].turn_on()
		if(mode is 3):
			self.assign_right_return_controls()
			self.show_message('Mixer Split:Right Side Faders = Returns 1-4, Dials = Returns Pan')
		else:	##(mode in range(0, 3):
			self.assign_right_volume_controls()
			#self._mixer2.set_track_offset(4 + (mode*4))
			self._session2.set_offsets(int(self._mem[mode]), self._session2._scene_offset)
			self.show_message('Mixer Split:Right Side Faders = Channel Mixer, Dials = Returns, Track Offset' + str(self._mem[mode]))
			self._ohm_type = OHM_TYPE[mode]
			self._ohm = OHM_VALUE[mode]
#		elif(mode is 2):
#			self.assign_right_user1_controls()
#			self.show_message('Mixer Split:Right Side Faders = Returns 1-4, Dials = User Map')
#		elif(mode is 3):
#			self.assign_right_user2_controls()
#			self.show_message('Mixer Split:Right Side Faders = User Map, Dials = User Map')
	

	def m_function_update(self):
		#self.log_message('m_function_update '+ str(self._m_function_mode._mode_index))
		mode = self._m_function_mode._mode_index
		if(self._m_function_mode.is_enabled() is False):
			self._m_function_mode.set_mode_buttons(None)
			self._session.set_show_highlight(False)
			self._session2.set_show_highlight(False)
			self._session_main._highlighting_callback(self._session_main._track_offset, self._session_main._scene_offset, 8, 5, 1)
		elif(self._m_function_mode.is_enabled() is True):
			if(len(self._m_function_mode._modes_buttons) is 0):
				for index in range(8):
					self._mixer.channel_strip(index).set_select_button(None)
				buttons = []
				for index in range(4):
					buttons.append(self._button[index]) 
				self._m_function_mode.set_mode_buttons(tuple(buttons))
			if(self._shift_mode._mode_index is 4):
				for index in range(4):
					if(mode != index):
						self._button[index].turn_off()
					else:
						self._button[index].turn_on()
		if(mode is 0):
			self.assign_main_controls1()
			self.show_message('Mixer Linked:Dials in Device(Top) and Selected Send(Bottom) Mode')
		elif(mode is 1):
			self.assign_main_controls2()
			self.show_message('Mixer Linked:Dials in Channel Send Mode (Sends 1-3)')
		elif(mode is 2):
			self.assign_main_controls3()
			self.show_message('Mixer Linked:Left Dials in Filter(Top) and Pan(Bottom) Mode')
		elif(mode is 3):
			self.assign_main_controls4()
			self.show_message('Mixer Linked:Dials in User Map Mode')
	

	def shift_update(self):
		self._clutch_device_selection = True
		self.allow_updates(False)
		if(not self._in_build_midi_map):
			self.set_suppress_rebuild_requests(True)
		self.deassign_channel_select_buttons()
		self.deassign_matrix()
		self.deassign_menu()
		if(self._monomod_mode._mode_index is 0):		#if monomod is not on
			if(self._shift_mode._mode_index is 0):							#if no shift is pressed
				self._shift_mode._mode_toggle1.turn_off()
				self._shift_mode._mode_toggle2.turn_off()
				if(self.split_mixer() is False):
					self.set_split_mixer(True)
				for zoom in self._zooms:
					zoom._zoom_value(0)
				self.zoom_off()
				self._device_selector.set_enabled(False)
				for mode in self._function_modes:
					mode.set_enabled(False)
				self.assign_channel_select_buttons()
				self._recalculate_selected_channel()
				self.assign_session_nav_to_menu()
				self.assign_lower_grid_names(0)
				self.l_function_update()
				self.r_function_update()
				self._session.set_show_highlight(True)
			elif(self._shift_mode._mode_index is 1):						#if no shift is pressed, but mixer is linked
				self._shift_mode._mode_toggle1.turn_on()
				self._shift_mode._mode_toggle2.turn_on()
				if(self.split_mixer() is True):
					self.set_split_mixer(False)
				for zoom in self._zooms:
					zoom._zoom_value(0)
				self.zoom_off_m()
				self._device_selector.set_enabled(False)
				self.m_function_update()
				for mode in self._function_modes:
					mode.set_enabled(False)
				self.assign_main_channel_select_buttons()
				self.assign_session_main_nav_to_menu()
				self.assign_lower_grid_names(0)
				self._session_main.set_show_highlight(True)
			elif(self._shift_mode._mode_index > 1):						#if a shift is pressed
				self.assign_device_nav_to_menu()
				self.deassign_channel_select_buttons()
				if(self._shift_mode._mode_index is 2):					#if shift left
					self._shift_mode._mode_toggle1.turn_on()
					self.zoom_left()
					self.assign_lower_grid_names(1)
					self._session_zoom._zoom_value(1)
					self._session.set_enabled(True) #this is a workaround so that the stop buttons still function
					self._l_function_mode.set_enabled(True)
					self._session.set_show_highlight(True)
				elif(self._shift_mode._mode_index is 3):				#if shift right
					self._shift_mode._mode_toggle2.turn_on()
					self.zoom_right()
					self.assign_lower_grid_names(1)
					self._session_zoom2._zoom_value(1)
					self._session2.set_enabled(True)  #this is a workaround so that the stop buttons still function
					self._r_function_mode.set_enabled(True)
					self.assign_shift_controls()
					if(self._r_function_mode._mode_index is 0):
						self._session2.set_show_highlight(True)
				elif(self._shift_mode._mode_index is 4):				#if either shift pressed while mixer is linked
					self._shift_mode._mode_toggle1.turn_on()
					self._shift_mode._mode_toggle2.turn_on()
					self.zoom_main()
					self.assign_lower_grid_names(1)
					self._session_zoom_main._zoom_value(1)
					self._session_main.set_enabled(True) #this is a workaround so that the stop buttons still function
					self._m_function_mode.set_enabled(True)
					self.assign_shift_controls()
					self._session_main.set_show_highlight(True)
				self._device_selector.set_enabled(True)
		else:
			self.assign_lower_grid_names(3)
			if(self._shift_mode._mode_index is 0):							#if no shift is pressed
				self._shift_mode._mode_toggle1.turn_off()
				self._shift_mode._mode_toggle2.turn_off()
				if(self.split_mixer() is False):
					self.set_split_mixer_monomod(True)
				self._device_selector.set_enabled(False)
				for mode in self._function_modes:
					mode.set_enabled(False)
				self.l_function_update()
				self.r_function_update()
				self.assign_channel_select_buttons()
				self.assign_monomod_to_menu()			##this only assigns the names...they use deactivation instead of reassingment
			elif(self._shift_mode._mode_index is 1):						#if no shift is pressed, but mixer is linked
				self._shift_mode._mode_toggle1.turn_on()
				self._shift_mode._mode_toggle2.turn_on()
				if(self.split_mixer() is True):
					self.set_split_mixer(False)
				self._device_selector.set_enabled(False)
				for mode in self._function_modes:
					mode.set_enabled(False)
				self.m_function_update()
				self.assign_main_channel_select_buttons()
				self.assign_monomod_to_menu()				##this only assigns the names...they use deactivation instead of reassingment
			elif(self._shift_mode._mode_index > 1):						#if a shift is pressed
				self.deassign_channel_select_buttons()
				self.assign_monomod_shift_to_menu()
				if(self._shift_mode._mode_index is 2):					#if shift left
					self._shift_mode._mode_toggle1.turn_on()
					for index in range(4):
						self._button[index + 4]._off_value = DEVICE_SELECT[self._rgb]
					self._device_selector.assign_buttons(tuple(self._button[index + 4] for index in range(4)), 4)
					self._l_function_mode.set_enabled(True)
					self._session.set_show_highlight(True)
				elif(self._shift_mode._mode_index is 3):				#if shift right
					self._shift_mode._mode_toggle2.turn_on()
					for index in range(4):
						self._button[index]._off_value = DEVICE_SELECT[self._rgb]
					self._device_selector.assign_buttons(tuple(self._button[index] for index in range(4)), 0)
					self._r_function_mode.set_enabled(True)
					self.assign_shift_controls()
					if(self._r_function_mode._mode_index < 4):
						self._session2.set_show_highlight(True)
				elif(self._shift_mode._mode_index is 4):				#if either shift pressed while mixer is linked
					self._shift_mode._mode_toggle1.turn_on()
					self._shift_mode._mode_toggle2.turn_on()
					for index in range(4):
						self._button[index + 4]._off_value = DEVICE_SELECT[self._rgb]
					self._device_selector.assign_buttons(tuple(self._button[index + 4] for index in range(4)), 4)
					self._m_function_mode.set_enabled(True)
					self.assign_shift_controls()
					self._session_main.set_show_highlight(True)
				self._device_selector.set_enabled(True)
			if self._shift_mode._mode_index > 1:
				self._host._shift_value(1)
			else:
				self._host._shift_value(0)
		self.allow_updates(True)
		self.set_suppress_rebuild_requests(False)
		self._clutch_device_selection = False
	


	"""left control management methods"""
	def deassign_left_dials(self):
		for index in range(12):
			self._dial[index].use_default_message()
			self._dial[index].release_parameter()
			self._dial[index].set_enabled(True)
		if(self._device._parameter_controls != None):
			for control in self._device._parameter_controls:
				control.release_parameter()
			self._device._parameter_controls = None
		self._mixer.selected_strip().set_send_controls(None)
		for track in range(4):
			self._mixer.channel_strip(track).set_send_controls(None)
			self._mixer.channel_strip(track).set_pan_control(None)
	

	def assign_left_device_dials(self):
		self._backlight_type = BACKLIGHT_TYPE[0]
		self._backlight = BACKLIGHT_VALUE[0]
		self.deassign_left_dials()
		self._device.set_enabled(True)
		device_param_controls = []
		for index in range(8):
			device_param_controls.append(self._dial[index])
		self._device.set_parameter_controls(tuple(device_param_controls))
		dials = []
		for index in range(4):
			dials.append(self._dial[index + 8])
		self._mixer.selected_strip().set_send_controls(tuple(dials))
	

	def assign_left_send_dials(self):
		self._backlight_type = BACKLIGHT_TYPE[1]
		self._backlight = BACKLIGHT_VALUE[1]
		self.deassign_left_dials()
		for track in range(4):
			channel_strip_send_controls = []
			for control in range(3):
				channel_strip_send_controls.append(self._dial[track + (control * 4)])
			self._mixer.channel_strip(track).set_send_controls(tuple(channel_strip_send_controls))
	

	def assign_left_filter_dials(self):
		self._backlight_type = BACKLIGHT_TYPE[2]
		self._backlight = BACKLIGHT_VALUE[2]
		self.deassign_left_dials()
		for index in range(4):
			self._mixer.track_filter(index).set_filter_controls(self._dial[index], self._dial[index + 4])
		for track in range(4):
			self._mixer.channel_strip(track).set_pan_control(self._dial[track + 8])
	

	def assign_left_user_dials(self):
		self._backlight_type = BACKLIGHT_TYPE[3]
		self._backlight = BACKLIGHT_VALUE[3]
		self.deassign_left_dials()
		for index in range(12):
			self._dial[index].set_channel(L_USER_DIAL_CHAN)
			self._dial[index].set_identifier(L_USER_DIAL_MAP[index])
			self._dial[index].set_enabled(False)
	


	"""right control management methods"""
	def deassign_right_controls(self):
		self._mixer.master_strip().set_volume_control(None)
		self._mixer.set_prehear_volume_control(None)
		for index in range(4):
			self._mixer.channel_strip(index + 4).set_volume_control(None)
			self._mixer2.channel_strip(index).set_volume_control(None)
			self._mixer2.return_strip(index).set_volume_control(None)
			self._mixer2.return_strip(index).set_pan_control(None)
			self._mixer2.selected_strip().set_send_controls(None)
			self._dial[index + 12].use_default_message()
			self._fader[index + 4].use_default_message()
			self._dial[index + 12].release_parameter()
			self._fader[index + 4].release_parameter()
			self._fader[index + 4].set_enabled(True)
			self._dial[index + 12].set_enabled(True)
	

	def assign_right_volume_controls(self):
		self._ohm_type = OHM_TYPE[0]
		self._ohm = OHM_VALUE[0]
		self.deassign_right_controls()
		for index in range(4):
			if(self._mixer2.channel_strip(index)):
				self._mixer2.channel_strip(index).set_volume_control(self._fader[index + 4])
		for index in range(4):
			if(self._mixer2.return_strip(index)):
				self._mixer2.return_strip(index).set_volume_control(self._dial[index + 12])
	

	def assign_right_return_controls(self):
		self._ohm_type = OHM_TYPE[1]
		self._ohm = OHM_VALUE[1]
		self.deassign_right_controls()
		#need to turn off session2 and session_zoom2 here, and in all subsequent right side modes
		#self._session_main._highlighting_callback(len(self.song.song.tracks), self._session2._scene_offset, 4, 5, 1)
		self._session2.set_show_highlight(False)
		for index in range(4):
			if(self._mixer2.return_strip(index)):
				self._mixer2.return_strip(index).set_volume_control(self._fader[index + 4])
				self._mixer2.return_strip(index).set_pan_control(self._dial[index + 12])
	


	"""main control management methods"""
	def assign_main_controls1(self):
		self.deassign_right_controls()
		self.deassign_left_dials()
		for column in range(8):
			self._mixer.channel_strip(column).set_volume_control(self._fader[column])
		self.assign_left_device_dials()
		for index in range(4):
			self._mixer2.return_strip(index).set_volume_control(self._dial[index + 12])
	

	def assign_main_controls2(self):
		self.deassign_right_controls()
		self.deassign_left_dials()
		for column in range(8):
			self._mixer.channel_strip(column).set_volume_control(self._fader[column])
		self.assign_left_send_dials()
		for index in range(4):
			self._mixer2.return_strip(index).set_volume_control(self._dial[index + 12])
	

	def assign_main_controls3(self):
		self.deassign_right_controls()
		self.deassign_left_dials()
		for column in range(8):
			self._mixer.channel_strip(column).set_volume_control(self._fader[column])
		self.assign_left_filter_dials()
		for index in range(4):
			self._mixer2.return_strip(index).set_volume_control(self._dial[index + 12])
	

	def assign_main_controls4(self):
		self.deassign_right_controls()
		self.deassign_left_dials()
		for column in range(8):
			self._mixer.channel_strip(column).set_volume_control(self._fader[column])
		self.assign_left_user_dials()
		for index in range(4):
			self._mixer2.return_strip(index).set_volume_control(self._dial[index + 12])
	


	"""menu button management methods"""
	def deassign_menu(self):
		for index in range(6):
			self._menu[index].set_on_off_values(127, 0)
		self._device.set_lock_button(None)
		self._device.set_on_off_button(None)
		self._device_navigator.set_device_nav_buttons(None, None)	
		self._device.set_bank_nav_buttons(None, None)
		self._transport.set_play_button(None)	
		self._transport.set_record_button(None) 
		self._transport.set_stop_button(None)
		self._transport.set_loop_button(None)	
		self._transport.set_overdub_button(None)	
		session.set_stop_all_clips_button(None)
		self._transport.set_play_button(None)	
		self._transport.set_stop_button(None)
		self._session_main.set_track_bank_buttons(None, None)
		self._session_main.set_scene_bank_buttons(None, None)
	

	def assign_device_nav_to_menu(self):
		self._menu[2].set_on_value(DEVICE_LOCK[self._rgb])
		self._device.set_lock_button(self._menu[2])
		self._menu[1].set_on_value(DEVICE_ON[self._rgb])
		self._device.set_on_off_button(self._menu[1])
		for index in range(2):
			self._menu[index + 4].set_on_value(DEVICE_NAV[self._rgb])
			self._menu[index * 3].set_on_value(DEVICE_BANK[self._rgb])
		self._device_navigator.set_device_nav_buttons(self._menu[4], self._menu[5]) 
		self._device.set_bank_nav_buttons(self._menu[0], self._menu[3])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(DEVICE_NAV_NAMES[index])))
	

	def assign_transport_to_menu(self):
		self._menu[0].set_on_off_values(PLAY_ON[self._rgb], PLAY[self._rgb])
		self._transport.set_play_button(self._menu[0])	
		self._menu[2].set_on_value(RECORD[self._rgb])
		self._transport.set_record_button(self._menu[2])
		self._menu[1].set_on_value(STOP[self._rgb])
		self._transport.set_stop_button(self._menu[1])
		self._menu[3].set_on_value(LOOP[self._rgb])
		self._transport.set_loop_button(self._menu[3])	
		self._menu[5].set_on_value(OVERDUB[self._rgb])
		self._transport.set_overdub_button(self._menu[5])
		self._menu[4].set_on_value(STOP_ALL[self._rgb])
		session.set_stop_all_clips_button(self._menu[4])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(TRANSPORT_NAMES[index])))
	

	def assign_session_nav_to_menu(self):
		self._menu[1].set_on_off_values(PLAY_ON[self._rgb], PLAY[self._rgb])
		self._transport.set_play_button(self._menu[1])	
		self._menu[2].set_on_off_values(STOP[self._rgb], STOP[self._rgb])	
		self._transport.set_stop_button(self._menu[2])
		for index in range(2):
			self._menu[index + 4].set_on_value(SESSION_NAV[self._rgb])
			self._menu[index * 3].set_on_value(SESSION_NAV[self._rgb])
		self._session.set_track_bank_buttons(self._menu[5], self._menu[4])
		self._session.set_scene_bank_buttons(self._menu[3], self._menu[0])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(SESSION_NAV_NAMES[index])))
	

	def assign_session2_nav_to_menu(self):
		self._menu[1]._on_value = PLAY[self._rgb]
		#self._menu[1]._off_value = 0
		self._transport.set_play_button(self._menu[1])	
		self._menu[2]._on_value = STOP[self._rgb]	
		#self._menu[2]._off_value = STOP[self._rgb]	
		self._transport.set_stop_button(self._menu[2])
		for index in range(2):
			self._menu[index + 4]._on_value = SESSION_NAV[self._rgb]
			self._menu[index * 3]._on_value = SESSION_NAV[self._rgb]
		self._session.set_track_bank_buttons(self._menu[5], self._menu[4])
		self._session.set_scene_bank_buttons(self._menu[3], self._menu[0])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(SESSION_NAV_NAMES[index])))
	

	def assign_session_main_nav_to_menu(self):
		self._menu[1]._on_value = PLAY[self._rgb]
		#self._menu[1]._off_value = 0
		self._transport.set_play_button(self._menu[1])	
		self._menu[2]._on_value = STOP[self._rgb]	
		#self._menu[2]._off_value = STOP[self._rgb]	
		self._transport.set_stop_button(self._menu[2])
		for index in range(2):
			self._menu[index + 4]._on_value = SESSION_NAV[self._rgb]
			self._menu[index * 3]._on_value = SESSION_NAV[self._rgb]
		self._session_main.set_track_bank_buttons(self._menu[5], self._menu[4])
		self._session_main.set_scene_bank_buttons(self._menu[3], self._menu[0])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(SESSION_NAV_NAMES[index])))
	

	def assign_monomod_shift_to_menu(self):
		self._menu[1].set_on_off_values(PLAY_ON[self._rgb], PLAY[self._rgb])
		self._transport.set_play_button(self._menu[1])
		self._menu[2].set_on_off_values(STOP[self._rgb], STOP[self._rgb])		
		self._transport.set_stop_button(self._menu[2])
		for index in range(2):
			self._menu[index + 4].set_on_value(DEVICE_NAV[self._rgb])
			self._menu[index * 3].set_on_value(DEVICE_BANK[self._rgb])
		self._device_navigator.set_device_nav_buttons(self._menu[4], self._menu[5]) 
		self._device.set_bank_nav_buttons(self._menu[0], self._menu[3])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(MONOMOD_SHIFT_NAMES[index])))
	

	def assign_monomod_to_menu(self):
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(MONOMOD_NAMES[index])))
	

	def assign_session_bank_to_menu(self):
		self._menu[1].set_on_off_values(PLAY_ON[self._rgb], PLAY[self._rgb])
		self._transport.set_play_button(self._menu[0])	
		self._menu[2].set_on_off_values(STOP[self._rgb], STOP[self._rgb])	
		self._transport.set_stop_button(self._menu[1])
		for index in range(2):
			self._menu[index + 4].set_on_value(BANK_BUTTONS[self._rgb])
			self._menu[index * 3].set_on_value(BANK_BUTTONS[self._rgb])
		self._session.set_track_bank_buttons(self._menu[5], self._menu[4])
		self._session.set_scene_bank_buttons(self._menu[3], self._menu[0])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(SESSION_BANK_NAMES[index])))
	

	def assign_session2_bank_to_menu(self):
		self._menu[1].set_on_off_values(PLAY_ON[self._rgb], PLAY[self._rgb])
		self._transport.set_play_button(self._menu[0])
		self._menu[2].set_on_off_values(STOP[self._rgb], STOP[self._rgb])
		self._transport.set_stop_button(self._menu[1])
		for index in range(2):
			self._menu[index + 4].set_on_value(BANK_BUTTONS[self._rgb])
			self._menu[index * 3].set_on_value(BANK_BUTTONS[self._rgb])
		self._session2.set_track_bank_buttons(self._menu[5], self._menu[4])
		self._session2.set_scene_bank_buttons(self._menu[3], self._menu[0])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(SESSION_BANK2_NAMES[index])))
	

	def assign_session_main_nav_to_menu(self):
		self._menu[1].set_on_off_values(PLAY_ON[self._rgb], PLAY[self._rgb])
		self._transport.set_play_button(self._menu[0])	
		self._menu[2].set_on_off_values(STOP[self._rgb], STOP[self._rgb])
		self._transport.set_stop_button(self._menu[1])
		for index in range(2):
			self._menu[index + 4].set_on_value(BANK_BUTTONS[self._rgb])
			self._menu[index * 3].set_on_value(BANK_BUTTONS[self._rgb])
		self._session_main.set_track_bank_buttons(self._menu[5], self._menu[4])
		self._session_main.set_scene_bank_buttons(self._menu[3], self._menu[0])
		for index in range(6):
			self._monobridge._send_osc(self._menu[index].osc_name, self.generate_strip_string(str(SESSION_MAIN_BANK_NAMES[index])))
	


	"""channel selection management methods"""
	def deassign_channel_select_buttons(self):
		for index in range(8):
			if(self._mixer.channel_strip(index)):
				self._mixer.channel_strip(index).set_select_button(None)
			self._button[index].release_parameter()
		for index in range(4):
			self._mixer2.channel_strip(index).set_select_button(None)
			self._mixer2.return_strip(index).set_select_button(None)
			self._mixer2.master_strip().set_select_button(None)
			self._button[index + 4].release_parameter()
	

	def assign_channel_select_buttons(self):
		for index in range(4):
			#if(self._mixer.channel_strip(index)):
			self._button[index].set_on_off_values(127, 0)
			self._mixer.channel_strip(index).set_select_button(self._button[index])
		if(self._r_function_mode._mode_index < 3):
			for index in range(4):
				#if(self._mixer2.channel_strip(index)):
				self._button[index].set_on_off_values(127, 0)
				self._mixer2.channel_strip(index).set_select_button(self._button[index + 4])	
		#elif(self._r_function_mode._mode_index < 3):
		else:
			for index in range(4):
				#if(self._mixer2.return_strip(index)):
				self._button[index].set_on_off_values(1, 0)
				self._mixer2.return_strip(index).set_select_button(self._button[index + 4])
	

	def assign_return_select_buttons(self):
		for index in range(4):
			self._button[index + 4].set_off_value(0)
			if(self._mixer.channel_strip(index)):
				self._button[index + 4].set_on_value(1)
				self._mixer.channel_strip(index).set_select_button(self._button[index + 4])
	

	def assign_l_channel_select_buttons(self):
		self._mixer.set_select_buttons(None, None)
		self._session.set_select_buttons(None, None)
		for index in range(4):
			self._button[index].set_off_value(0)
			if(self._mixer.channel_strip(index)):
				self._mixer.channel_strip(index).set_select_button(self._button[index])
	

	def assign_r_channel_select_buttons(self):
		self._mixer2.set_select_buttons(None, None)
		self._session2.set_select_buttons(None, None)
		for index in range(4):
			self._button[index + 4].set_off_value(0)
			if(self._mixer2.channel_strip(index)):
				self._mixer2.channel_strip(index).set_select_button(self._button[index + 4])
	

	def assign_main_channel_select_buttons(self):
		for index in range(8):
			self._button[index].set_off_value(0)
			if(self._mixer.channel_strip(index)):
				self._button[index].set_on_value(127)
				self._mixer.channel_strip(index).set_select_button(self._button[index])
	

	def assign_shift_controls(self):
		self.deassign_right_controls()
		self._mixer.master_strip().set_volume_control(self._fader[7])
		self._mixer.set_prehear_volume_control(self._dial[15])	
	



	"""called on timer"""
	def update_display(self):
		""" Live -> Script
		Aka on_timer. Called every 100 ms and should be used to update display relevant
		parts of the controller
		"""
		for message in self._scheduled_messages:
			message['Delay'] -= 1
			if (message['Delay'] == 0):
				if (message['Parameter'] != None):
					message['Message'](message['Parameter'])
				else:
					message['Message']()
					del self._scheduled_messages[self._scheduled_messages.index(message)]

		for callback in self._timer_callbacks:
			callback()
		self._timer = (self._timer + 1) % 256
		self.flash()
	

	def flash(self):
		#if(self.flash_status > 0):
		for row in range(8):
			if(self._button[row]._flash_state > 0):
				self._button[row].flash(self._timer)
				self._bank_button[row].flash(self._timer)
				self._key_button[row].flash(self._timer)
			for column in range(8):
				button = self._grid[column][row]
				if(button._flash_state > 0):
					button.flash(self._timer)
		for column in range(16):
			for row in range(16):
				self._square[column][row].flash(self._timer)
	

	def strobe(self):
		if(self._backlight_type != 'static'):
			if(self._backlight_type is 'pulse'):
				self._backlight = int(math.fabs(((self._timer * 16) % 64) -32) +32)
			if(self._backlight_type is 'up'):
				self._backlight = int(((self._timer * 8) % 64) + 16)
			if(self._backlight_type is 'down'):
				self._backlight = int(math.fabs(int(((self._timer * 8) % 64) - 64)) + 16)
		self._send_midi(tuple([176, 27, int(self._backlight)]))
		if(self._ohm_type != 'static'):
			if(self._ohm_type is 'pulse'):
				self._ohm = int(math.fabs(((self._timer * 16) % 64) -32) +32)
			if(self._ohm_type is 'up'):
				self._ohm = int(((self._timer * 8) % 64) + 16)
			if(self._ohm_type is 'down'):
				self._ohm = int(math.fabs(int(((self._timer * 8) % 64) - 64)) + 16)
		self._send_midi(tuple([176, 63, int(self._ohm)]))
		self._send_midi(tuple([176, 31, int(self._ohm)]))	
	


	"""m4l bridge"""
	def generate_strip_string(self, display_string):
		try:
			display_string = str(display_string)
		except:
			return ' ? '
		else:
			NUM_CHARS_PER_DISPLAY_STRIP = 9
			if (not display_string):
				#return (' ' * NUM_CHARS_PER_DISPLAY_STRIP)
				return ('`_')
			if ((len(display_string.strip()) > (NUM_CHARS_PER_DISPLAY_STRIP - 1)) and (display_string.endswith('dB') and (display_string.find('.') != -1))):
				display_string = display_string[:-2]
			if (len(display_string) > (NUM_CHARS_PER_DISPLAY_STRIP - 1)):
				for um in [' ',
				 'i',
				 'o',
				 'u',
				 'e',
				 'a']:
					while ((len(display_string) > (NUM_CHARS_PER_DISPLAY_STRIP - 1)) and (display_string.rfind(um, 1) != -1)):
						um_pos = display_string.rfind(um, 1)
						display_string = (display_string[:um_pos] + display_string[(um_pos + 1):])
			else:
				display_string = display_string.center((NUM_CHARS_PER_DISPLAY_STRIP - 1))
			ret = u''
			for i in range((NUM_CHARS_PER_DISPLAY_STRIP - 1)):
				if ((ord(display_string[i]) > 127) or (ord(display_string[i]) < 0)):
					ret += ' '
				else:
					ret += display_string[i]

			ret += ' '
			assert (len(ret) == NUM_CHARS_PER_DISPLAY_STRIP)
			return '`' + ret.replace(' ', '_')
	

	def notification_to_bridge(self, name, value, sender):
		if(isinstance(sender, MonoEncoderElement2)):
			#self.log_message(str(name) + str(value) + str(sender.num))
			self._monobridge._send('lcd_name', sender.name, self.generate_strip_string(str(name)))
			self._monobridge._send('lcd_value', sender.name, self.generate_strip_string(str(value)))
	

	def clip_name(self, sender, name):
		self._monobridge._send_osc(sender.osc_name, self.generate_strip_string(str(name)))
	

	def old_notification_to_bridge(self, value, sender):
		if(isinstance(sender, MonoEncoderElement)):
			#self._monobridge._button_value('notification', 'fader', value, [sender.num, str(sender._parameter_to_map_to.name), str(sender.mapped_parameter())])
			if sender._parameter_to_map_to != None:
				if isinstance(sender._parameter_to_map_to, Live.DeviceParameter.DeviceParameter):
					if str(sender._parameter_to_map_to.original_name) == 'Track Volume':
						self._monobridge._button_value('fader', sender.num,	 str(sender._parameter_to_map_to.canonical_parent.canonical_parent.name), str(sender.mapped_parameter()))
					else: 
						self._monobridge._button_value('fader', sender.num, str(sender._parameter_to_map_to.name), str(sender.mapped_parameter()))
			else:
				self._monobridge._button_value('fader', sender.num, ' ', ' ')
		else:
			#self.log_message(str(sender._parameter_to_map_to) + str(type(sender._parameter_to_map_to)))
			if sender._parameter_to_map_to != None:
				if isinstance(sender._parameter_to_map_to, Live.DeviceParameter.DeviceParameter):
					if str(sender._parameter_to_map_to.original_name) == 'Track Volume':
						self._monobridge._button_value('dial', sender.num,	str(sender._parameter_to_map_to.canonical_parent.canonical_parent.name), str(sender.mapped_parameter()))
					else: 
						self._monobridge._button_value('dial', sender.num, str(sender._parameter_to_map_to.name), str(sender.mapped_parameter()))
			else:
				self._monobridge._button_value('dial', sender.num, ' ', ' ')
	

	def get_clip_names(self):
		clip_names = []
		for scene in self._session._scenes:
			for clip_slot in scene._clip_slots:
				if clip_slot.has_clip():
					clip_names.append(clip_slot._clip_slot)##.clip.name)
					return clip_slot._clip_slot
					##self.log_message(str(clip_slot._clip_slot.clip.name))
		return clip_names
	


	"""midi functionality"""
	def max_to_midi(self, message): #takes a 'tosymbol' list from Max, such as "240 126 0 6 1 247"
		msg_str = str(message) #gets rid of the quotation marks which 'tosymbol' has added
		midi_msg = tuple(int(s) for s in msg_str.split()) #converts to a tuple 
		self._send_midi(midi_msg) #sends to controller
	

	def max_from_midi(self, message): #takes a 'tosymbol' list from Max, such as "240 126 0 6 1 247"
		msg_str = str(message) #gets rid of the quotation marks which 'tosymbol' has added
		midi_msg = tuple(int(s) for s in msg_str.split()) #converts to a tuple 
		self.receive_external_midi(midi_msg) #sends to controller
	

	def to_encoder(self, num, val):
		rv=int(val*127)
		self._device._parameter_controls[num].receive_value(rv)
		p = self._device._parameter_controls[num]._parameter_to_map_to
		newval = (val * (p.max - p.min)) + p.min
		p.value = newval
	

	def receive_external_midi(self, midi_bytes):
		#self.log_message('receive_external_midi' + str(midi_bytes))
		assert (midi_bytes != None)
		assert isinstance(midi_bytes, tuple)
		self.set_suppress_rebuild_requests(True)
		if (len(midi_bytes) is 3):
			msg_type = (midi_bytes[0] & 240)
			forwarding_key = [midi_bytes[0]]
			self.log_message(str(self._forwarding_registry))
			if (msg_type is not MIDI_PB_TYPE):
				forwarding_key.append(midi_bytes[1])
			recipient = self._forwarding_registry[tuple(forwarding_key)]
			self.log_message('receive_midi recipient ' + str(recipient))
			if (recipient != None):
				recipient.receive_value(midi_bytes[2])
		else:
			self.handle_sysex(midi_bytes)
		self.set_suppress_rebuild_requests(False)
	


	"""general functionality"""
	def disconnect(self):
		"""clean things up on disconnect"""
		self.song().view.remove_selected_track_listener(self._update_selected_device)
		self._update_linked_device_selection = None
		self._session2.remove_offset_listener(self._on_session_offset_changes)
		#self._disconnect_notifier.set_mode(0)
		self.log_message("--------------= AumPad log closed =--------------") #Create entry in log file
		self._mixers = []
		self._sessions = []
		self._zooms = []
		self._function_modes = []
		ControlSurface.disconnect(self)
		return None
	

	def allow_updates(self, allow_updates):
		for component in self.components:
			component.set_allow_update(int(allow_updates!=0))
	

	def device_follows_track(self, val):
		self._device_selection_follows_track_selection = (val == 1)
		return self
	

	def _update_selected_device(self):
		if self._device_selection_follows_track_selection is True:
			if(self._clutch_device_selection == False):
				track = self.song().view.selected_track
				device_to_select = track.view.selected_device
				if device_to_select == None and len(track.devices) > 0:
					device_to_select = track.devices[0]
				if device_to_select != None:
					self.song().view.select_device(device_to_select)
				#self._device.set_device(device_to_select)
				self.set_appointed_device(device_to_select)
				#self._device_selector.set_enabled(True)
				self.request_rebuild_midi_map()
		return None 
	

	def assign_alternate_mappings(self):
		for column in range(8):
			for row in range(8):
				self._grid[column][row].set_identifier(OHM_MAP_ID[column][row])
				self._grid[column][row].set_identifier(OHM_MAP_CHANNEL[column][row])
				self._grid[column][row].send_value(OHM_MAP_VALUE[column][row])
				self._grid[column][row].set_enabled(False)
	

	def get_session_offsets(self):
		if(self._is_split is True):
			return [self._session.track_offset(), self._session.scene_offset(), self._session2.track_offset(), self._session2.scene_offset()]
		elif(self._is_split is False):
			return [self._session_main.track_offset(), self._session_main.scene_offset(), (self._session_main.track_offset()) + 4, self._session_main.scene_offset()]
	

	def set_split_mixer(self, is_split):
		assert isinstance(is_split, type(False))
		if(is_split!=self._is_split):
			if(is_split is True):
				self._mixer._track_offset = self._session._track_offset
			else:
				self._mixer._track_offset = self._session_main._track_offset
			self._is_split = is_split
			self._session_main.set_enabled(not is_split)
			self._session.set_enabled(is_split)
			self._session2.set_enabled(is_split)
			self._mixer._reassign_tracks()
	

	def set_split_mixer_monomod(self, is_split):
		assert isinstance(is_split, type(False))
		if(is_split!=self._is_split):
			if(is_split is True):
				self._mixer._track_offset = self._session._track_offset
			else:
				self._mixer._track_offset = self._session_main._track_offset
			self._is_split = is_split
			self._mixer._reassign_tracks()
	

	def split_mixer(self):
		return self._is_split
	

	def _get_num_tracks(self):
		return self.num_tracks
	

	def _recalculate_selected_channel(self):
		selected = False
		for index in range(4):
			if self.song().view.selected_track == self._mixer.channel_strip(index)._track:
				selected = True
			elif self.song().view.selected_track == self._mixer2.channel_strip(index)._track:
				selected = True
		if selected is False:
			self.song().view.selected_track = self._mixer2.channel_strip(0)._track
	

	def clear_grid_names(self):
		self.log_message('clear grid names' + str(self))
		for column in range(8):
			for row in range(8):
				self._monobridge._send_osc(self._grid[column][row]._osc_name, '`_')
	
	
	def _set_brightness(self, value):
		self._bright = (value != 0)
		for control in self.controls:
			if isinstance(control, OSCFlashingButtonElement):
				self._monobridge._send_osc(control.osc_alt, int(self._bright), True)
	

	def reset(self):
		for control in self.controls:
			control.reset()
	

	def assign_lower_grid_names(self, mode):
		if self._display_button_names is True:
			for column in range(8):
				for row in range(3):
					self._monobridge._send_osc(self._grid[column][row+5].osc_name, self.generate_strip_string(str(GRID_NAMES[mode][row][column])))
	

	def mixer_on_cf_assign_changed(self, channel_strip):
		def _on_cf_assign_changed():
			if (channel_strip.is_enabled() and (channel_strip._crossfade_toggle != None)):
				if (channel_strip._track != None) and (channel_strip._track in (channel_strip.song().tracks + channel_strip.song().return_tracks)):
					if channel_strip._track.mixer_device.crossfade_assign == 1: #modified
						channel_strip._crossfade_toggle.turn_off()
					elif channel_strip._track.mixer_device.crossfade_assign == 0:
						channel_strip._crossfade_toggle.send_value(5)
					else:
						channel_strip._crossfade_toggle.send_value(6)
		return _on_cf_assign_changed
	

	def _on_session_offset_changes(self):
		if self._r_function_mode._mode_index in range(0,3):
			self._mem[int(self._r_function_mode._mode_index)] = self._session2.track_offset()
	

	def device_is_banking_enabled(self, device):
		def _is_banking_enabled():
			return True
		return _is_banking_enabled
	
		
	def device_set_device(self, device_component):
		def _set_device(device):
			assert ((device == None) or isinstance(device, Live.Device.Device))
			if ((not device_component._locked_to_device) and (device != device_component._device)):
				if (device_component._device != None):
					device_component._device.remove_name_listener(device_component._on_device_name_changed)
					device_component._device.remove_parameters_listener(device_component._on_parameters_changed)
					parameter = device_component._on_off_parameter()
					if (parameter != None):
						parameter.remove_value_listener(device_component._on_on_off_changed)
					if (device_component._parameter_controls != None):
						for control in device_component._parameter_controls:
							control.release_parameter()
				device_component._device = device
				if (device_component._device != None):
					device_component._bank_index = 0
					device_component._device.add_name_listener(device_component._on_device_name_changed)
					device_component._device.add_parameters_listener(device_component._on_parameters_changed)
					parameter = device_component._on_off_parameter()
					if (parameter != None):
						parameter.add_value_listener(device_component._on_on_off_changed)
				for key in device_component._device_bank_registry.keys():
					if (key == device_component._device):
						device_component._bank_index = device_component._device_bank_registry.get(key, 0)
						del device_component._device_bank_registry[key]
						break
				device_component._bank_name = '<No Bank>' #added
				device_component._on_device_name_changed()
				device_component.update() 
			self._on_device_changed(device) 
		return _set_device
		
	

	def _on_device_changed(self, device):
		#self.log_message('new device ' + str(type(device)))
		if self._update_linked_device_selection != None:
			self._update_linked_device_selection(device)
	
