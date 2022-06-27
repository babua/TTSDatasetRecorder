# -*- coding: utf-8 -*-
import os
#os.environ['KIVY_TEXT'] = 'pil'  # noqa
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.core.text import FontContextManager as FCM

import queue
import sys

import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)

import soundcard as sc
from scipy.io.wavfile import write as wavwrite

from threading import Thread

SECOND_PER_CHAR = 0.1

class TTSDatasetRecorderWidget(Widget):
	sentence = StringProperty()
	progress_label = StringProperty()
	progress_goto = StringProperty()
	recording_indicator = StringProperty()
	reading_speed_text = StringProperty()
	reading_speed = NumericProperty()
	edit_text_button_text = StringProperty()
	second_per_char = SECOND_PER_CHAR

	
	def __init__(self, **kwargs):
		super(TTSDatasetRecorderWidget, self).__init__(**kwargs)
		self.line_index = -1
		self.book_file = "text.txt"
		with open(self.book_file, encoding="utf-8") as f:
			self.lines = [ line.replace("\n","") for line in f.readlines()]
		self.fs = 48000
		desktop_path = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 
		self.out_dir = os.path.join(desktop_path,"TTS_dataset_recordings")
		os.makedirs(self.out_dir,exist_ok=True)
		self.reading_speed_text = "Reading speed: %100"
		self.load_next_sentence()
		self.reading_speed = 100
		self.mic = sc.default_microphone()
		self.edit_text = False
		self.edit_text_button_text = "Edit Text"
		self.tmpSentence = ""

	def record_button(self):
		time_allowance = len(self.sentence) * self.second_per_char
		out_path = os.path.join(self.out_dir,f"{self.line_index+1}.wav")
		self.recording_indicator = "Recording..."

		t = Thread(target=self.record_audio, args=(out_path, time_allowance))
		t.daemon = True
		t.start()

	def record_audio(self,out_path,time_allowance):
		self.ids.record_button.disabled = True
		self.ids.reading_speed_slider.disabled = True
		self.ids.goto_text_input.disabled = True

		recording = self.mic.record(samplerate=self.fs, numframes=int(time_allowance * self.fs),channels=1)
		max_volume = numpy.max(numpy.abs(recording))
		if max_volume != 0:
			recording = recording / max_volume
			wavwrite(out_path, self.fs, recording)  # Save as WAV file
			self.recording_indicator = ""
		else:
			self.recording_indicator = "Nothing recorded. Check your microphone."
		self.ids.record_button.disabled = False
		self.ids.reading_speed_slider.disabled = False
		self.ids.goto_text_input.disabled = False
		self.load_next_sentence()
		

	def prev_button(self):
		self.line_index -= 2
		self.load_next_sentence()
	

	def load_next_sentence(self):
		self.line_index += 1
		if self.line_index >= len(self.lines):
			self.line_index = 0
		self.sentence = self.lines[self.line_index]
		self.progress_label = f"[{self.line_index+1}/{len(self.lines)}]"
		self.ids.goto_text_input.text = f"{self.line_index+1}"
		self.ids.goto_text_input.cursor = (0,0)

	def update_progress_textinput(self,*largs):
		self.progress_goto = f"{self.line_index+1}"

	def on_goto_line_text_enter(self,text):
		try:
			inp = int(text)-2
			if inp < -1:
				inp = -1
			if inp >= len(self.lines)-1:
				inp = len(self.lines) -2
			self.line_index = inp
		except Exception as e:
			print(e)
			self.line_index = self.line_index - 1
		print(self.line_index)
		self.load_next_sentence()

	def change_reading_speed(self, value):
		self.reading_speed = value
		speed_factor = 100. / float(self.reading_speed)
		self.second_per_char = SECOND_PER_CHAR * speed_factor
		self.reading_speed_text = f"Reading speed: %{self.reading_speed}"
		print(self.second_per_char)

	def toggle_text_input(self):
		app = App.get_running_app()
		
		if self.edit_text:
			self.ids["SentenceLabel"].width = app.root.width
			self.ids["SentenceLabel"].opacity = 1.
			self.ids["SentenceTextInput"].width = 0
			self.ids["SentenceTextInput"].opacity = 0.
			self.edit_text = False
			self.edit_text_button_text = "Edit Text"
			self.ids["SentenceTextInput"].text = self.ids["SentenceTextInput"].text.strip()
			if self.ids["SentenceTextInput"].text != self.sentence:
				self.sentence = self.ids["SentenceTextInput"].text
				self.lines[self.line_index] = self.sentence
				with open(self.book_file, "w", encoding="utf-8") as f:
					tmp_lines = [ x.strip()+"\n" for x in self.lines]
					f.writelines(tmp_lines)

		else:
			self.ids["SentenceLabel"].width = 0
			self.ids["SentenceLabel"].opacity = 0.
			self.ids["SentenceTextInput"].width = app.root.width
			self.ids["SentenceTextInput"].opacity = 1.
			self.edit_text = True
			self.edit_text_button_text = "Save Text"


class TTSDatasetRecorderApp(App):
	def build(self):
		return TTSDatasetRecorderWidget()


if __name__ == '__main__':
	TTSDatasetRecorderApp().run()


