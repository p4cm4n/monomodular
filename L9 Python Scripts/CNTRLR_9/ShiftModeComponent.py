import Live
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ModeSelectorComponent import ModeSelectorComponent
from FlashingButtonElement import FlashingButtonElement

class ShiftModeComponent(ModeSelectorComponent):
	__module__ = __name__
	__doc__ = ' Special Class that selects mode 0 if a mode button thats active is pressed'

	def __init__(self, script, callback):
		ModeSelectorComponent.__init__(self)
		self._script = script
		self.update = callback
		self._modes_buttons = []
		self._mode_index = 0
		self._last_mode = 0

	def set_mode_buttons(self, buttons):
		for button in self._modes_buttons:
			button.remove_value_listener(self._mode_value)
		self._modes_buttons = []
		if (buttons != None):
			for button in buttons:
				assert isinstance(button, ButtonElement or FlashingButtonElement)
				identify_sender = True
				button.add_value_listener(self._mode_value, identify_sender)
				self._modes_buttons.append(button)
	

	def number_of_modes(self):
		return 5
		
		
	def set_mode(self, mode):
		assert isinstance(mode, int)
		mode += 1
		assert (mode in range(self.number_of_modes()))
		if (self._mode_index != mode):
			self._mode_index = mode
			self.update()
		elif (self._mode_index != 0):
			self._mode_index = 0
			self.update()
	

	def _mode_value(self, value, sender):
		assert (len(self._modes_buttons) > 0)
		assert isinstance(value, int)
		assert isinstance(sender, ButtonElement)
		assert (self._modes_buttons.count(sender) == 1)
		if ((value is not 0) or (not sender.is_momentary())):
			self.set_mode(self._modes_buttons.index(sender))
	
# local variables:
# tab-width: 4