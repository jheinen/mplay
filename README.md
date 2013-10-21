mplay
=====

*Mplay* is a MIDI player written in pure *Python*. It runs on *OS X*, *Windows* and *Linux*. Apart from an *OpenGL* wrapper (for the GUI part), there are no dependencies on other packages. *Mplay* has been tested with *Python* 2.7.5, 3.3.2 and *PyOpenGL* 3.0.2.

**Hightlights:**

* Full functional MIDI player
* Mixer with mute and solo options
* Ability to change channel parameters (delay, chorus, reverb, pan)
* Volume sliders
* Pulldown menus for GM instrument sounds
* MIDI VU meter
* Show note, chord and lyrics information
* Change key, tempo
* Transport controls
* Keyboard shortcuts

**Tips and Tricks:**

*Mac OS X* and *Windows* systems come with a builtin software synthesizer (*Apple* DLS SoftSynth, *Microsoft* GS Wavetable SW Synth). On those systems *Mplay* runs out of the box. For *Linux*, however, it might be necessary to start a *TiMidity++* server:

	# sudo modprobe snd_virmidi
	# timidity -iAqqq &
	TiMidity starting in ALSA server mode
	Opening sequencer port: 128:0 128:1 128:2 128:3
	# aconnect -o
	client 0: 'System' [type=kernel]
        0 'Timer           '
        1 'Announce        '
	client 14: 'Midi Through' [type=kernel]
        0 'Midi Through Port-0'
	client 20: 'Virtual Raw MIDI 1-0' [type=kernel]
        0 'VirMIDI 1-0     '
	client 21: 'Virtual Raw MIDI 1-1' [type=kernel]
        0 'VirMIDI 1-1     '
	client 22: 'Virtual Raw MIDI 1-2' [type=kernel]
        0 'VirMIDI 1-2     '
	client 23: 'Virtual Raw MIDI 1-3' [type=kernel]
        0 'VirMIDI 1-3     '
	# aconnect 20:0 128:0


**Links:**

[*Mplay* website](http://josefheinen.de/mplay.html "Mplay website")

[Barcamp talk 2013](http://josefheinen.de/doc/Mplay_-_A_Python_MIDI_Mixer_-_Player_with_an_OpenGL_based_GUI.pdf "Lightning Talk at PythonCamp Cologne 2013, May 4-5 2013, GFU Cyrus")

