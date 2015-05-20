#!/usr/bin/env python

from __future__ import absolute_import, division

import sys
from math import sin, cos, atan2, pi
from time import sleep
from os.path import join, dirname

from OpenGL.GLUT import (glutAddMenuEntry, glutAddSubMenu, glutAttachMenu,
                         glutCreateMenu, glutCreateWindow, glutDisplayFunc,
                         glutIdleFunc, glutInit, glutInitDisplayMode,
                         glutInitWindowPosition, glutInitWindowSize,
                         glutKeyboardFunc, glutMainLoop, glutMotionFunc,
                         glutMouseFunc, glutSwapBuffers, glutPostRedisplay,
                         GLUT_DOUBLE, GLUT_DOWN, GLUT_LEFT_BUTTON, GLUT_RGB,
                         GLUT_RIGHT_BUTTON)
from OpenGL.GL import (glBegin, glEnd, glColor3f, glLoadIdentity, glMatrixMode,
                       glOrtho, glScale, glPixelStorei, glVertex2f,
                       glGenTextures, glBindTexture, glTexImage2D,
                       glTexParameteri, glTexCoord2f, glEnable, glDisable,
                       GL_TEXTURE, GL_TEXTURE_MIN_FILTER,
                       GL_TEXTURE_MAG_FILTER, GL_TEXTURE_2D, GL_LINES,
                       GL_NEAREST, GL_PROJECTION, GL_QUADS, GL_RGB,
                       GL_UNPACK_ALIGNMENT, GL_UNSIGNED_BYTE)

from smf import read, play, fileinfo, songinfo, beatinfo, lyrics, chordinfo, \
    setsong, channelinfo, setchannel, families, instruments

if sys.platform == 'darwin':
    from darwinmidi import midiDevice
elif sys.platform == 'win32':
    from win32midi import midiDevice
elif sys.platform == 'linux2':
    from linux2midi import midiDevice

MUTE_ON_OFF = {b'b': ['Bass'], b'g': ['Guitar'],
               b'k': ['Piano', 'Organ', 'Strings', 'Ensemble']}

SOLO_ON = {b'B': ['Bass'], b'G': ['Guitar'],
           b'K': ['Piano', 'Organ', 'Strings', 'Ensemble']}


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def read_image(path):
    f = open(path, 'rb')
    f.readline()  # magic number
    width, height = map(int, f.readline().split())
    f.readline()  # number of colors
    img = f.read(width * height * 3)
    f.close()
    img = b''.join(reversed([row for row in chunks(img, width * 3)]))
    return width, height, img


def copy_pixels(tox, toy, w, h, fromx, fromy):
    glEnable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glTexCoord2f(fromx, fromy)
    glVertex2f(tox, toy)
    glTexCoord2f(fromx+w, fromy)
    glVertex2f(tox+w, toy)
    glTexCoord2f(fromx+w, fromy+h)
    glVertex2f(tox+w, toy+h)
    glTexCoord2f(fromx, fromy+h)
    glVertex2f(tox, toy+h)
    glEnd()
    glDisable(GL_TEXTURE_2D)


def draw_text(x, y, s, color=0):
    for c in s:
        row = ord(c) // 16
        if ord(c) > 127:
            row -= 2
        fromx, fromy = (ord(c) % 16 * 7 + 770, 424 - row * 14)
        fromy += [0, -168, 168][color]
        copy_pixels(x, y, 7, 12, fromx, fromy)
        x += 7


def draw_line(x1, y1, x2, y2):
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()


def paint_knob(centerx, centery, value):
    angle = pi * (value - 64) / 64 * 0.75
    x, y = (centerx + 9 * sin(angle), centery + 9 * cos(angle))
    draw_line(centerx, centery + 9, x, y + 9)


def draw_rect(x, y, width, height):
    glColor3f(0.71, 0.83, 1)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    glColor3f(1, 1, 1)


def paint_notes(notes):
    key = (2, 10, 20, 33, 39, 57, 66, 76, 86, 94, 107, 113)
    for note in notes:
        x = 312 + key[note % 12]
        if (note % 12) in [1, 3, 6, 8, 10]:
            draw_rect(x, 48, 7, 24)
        else:
            draw_rect(x, 14, 10, 24)


class Player:
    def __init__(self, win, path, width, height):
        self.win = win
        self.midi = read(path)
        self.device = midiDevice()
        self.muted = 16 * [False]
        self.solo = 16 * [False]
        self.width = width
        self.height = height
        self.button = False
        self.selection = None
        self.pause = False

    def update(self):
        copy_pixels(0, 0, 730, 650, 0, 0)
        for channel in range(16):
            color = 0 if channel != self.selection else 2
            info = channelinfo(self.midi, channel)
            x = 10 + channel * 38
            if info['used']:
                name = info['name'] if channel != 9 else 'Drums'
                draw_text(620, 562 - channel * 14, name, color)
                if self.muted[channel]:
                    copy_pixels(x - 6, 633, 31, 11, 735, 633)
                if self.solo[channel]:
                    copy_pixels(x - 6, 619, 31, 10, 735, 619)
            paint_knob(x + 9, 581, info['sense'])
            draw_text(x, 559, '%3d' % info['sense'], color)
            paint_knob(x + 9, 523, info['delay'])
            draw_text(x, 501, '%3d' % info['delay'], color)
            paint_knob(x + 9, 465, info['chorus'])
            draw_text(x, 443, '%3d' % info['chorus'], color)
            paint_knob(x + 9, 407, info['reverb'])
            draw_text(x, 386, '%3d' % info['reverb'], color)
            pan = info['pan']
            paint_knob(x + 9, 349, pan)
            lr = 'L R'[(pan > 64) - (pan < 64) + 1]
            draw_text(x, 327, '%s%2d' % (lr, abs(pan - 64)), color)
            if info['used']:
                draw_text(x, 310, '%3d' % info['instrument'], color)
                draw_text(x - 5, 295, '%2d' % info['variation'], color)
                draw_text(x, 204, '%3d' % info['level'], color)
                copy_pixels(x + 13, 295, 12, 15, 754, 295)
                level = info['level']
            else:
                level = 0
            copy_pixels(x - 6, 204, 12, 91, 4, 204)
            copy_pixels(x - 6, 219 + level // 2, 12, 11, 735, 225)
            copy_pixels(x + 13, 219, 12, info['intensity'] // 2, 754, 219)
            if info['intensity'] >= 4:
                info['intensity'] -= 4
            else:
                info['intensity'] = 0

        draw_text(15, 177, fileinfo(self.midi))
        draw_text(15, 162, songinfo(self.midi))
        draw_text(15, 142, lyrics(self.midi), 1)
        chord, notes = chordinfo(self.midi)
        draw_text(15, 120, chord)
        paint_notes(notes)
        ticker = '            Python MIDI Player  \xa8 2013 by Josef Heinen '
        beat = beatinfo(self.midi)
        shift = beat % len(ticker.strip()) + 1
        if shift + 12 < len(ticker):
            draw_text(630, 628, ticker[shift: shift + 12])
        for led in range(4):
            if beat % 4 == led:
                copy_pixels(632 + led * 20, 309, 16, 30, 770, 585)
        if self.pause:
            copy_pixels(665, 251, 10, 10, 850, 604)
        else:
            copy_pixels(665, 251, 10, 10, 860, 604)

    def change_mute_state(self, channel):
        setchannel(self.midi, channel, muted=self.muted[channel])

    def change_solo_state(self, channel):
        self.solo[channel] = not self.solo[channel]
        if self.solo[channel]:
            setchannel(self.midi, channel, solo=self.solo[channel])
            for ch in range(16):
                self.muted[ch] = True if ch != channel else False
                self.solo[ch] = True if ch == channel else False
        else:
            for ch in range(16):
                self.muted[ch] = False
                setchannel(self.midi, ch, muted=False)

    def display_func(self):
        self.update()
        glutSwapBuffers()

    def keyboard_func(self, key, x, y):
        if key == b'\x1b':
            setsong(self.midi, action='exit')
            sys.exit(0)
        elif key == b'\t':
            if self.selection is not None:
                self.selection = (self.selection + 1) % 16
            else:
                self.selection = 0
            info = channelinfo(self.midi, self.selection)
            while not info['used']:
                self.selection = (self.selection + 1) % 16
                info = channelinfo(self.midi, self.selection)
        elif key == b' ':
            setsong(self.midi, action='pause')
            self.pause = not self.pause
        elif key in b'1234567890!@#$%^':
            channel = b'1234567890!@#$%^'.index(key)
            self.muted[channel] = not self.muted[channel]
            self.change_mute_state(channel)
        elif key == b'a':
            for channel in range(16):
                self.muted[channel] = self.solo[channel] = False
                self.change_mute_state(channel)
        elif key == b'd':
            self.muted[9] = not self.muted[9]
            self.change_mute_state(9)
        elif key == b'D':
            self.change_solo_state(9)
        elif key in MUTE_ON_OFF:
            for channel in range(16):
                info = channelinfo(self.midi, channel)
                if channel != 9 and info['family'] in MUTE_ON_OFF[key]:
                    self.muted[channel] = not self.muted[channel]
                self.change_mute_state(channel)
        elif key in SOLO_ON:
            for channel in range(16):
                info = channelinfo(self.midi, channel)
                if channel != 9 and info['family'] in SOLO_ON[key]:
                    self.muted[channel] = False
                else:
                    self.muted[channel] = True
                    self.solo[channel] = False
                self.change_mute_state(channel)
        elif key == b'<':
            setsong(self.midi, shift=-1)
        elif key == b'>':
            setsong(self.midi, shift=+1)
        elif key == b'-':
            setsong(self.midi, bpm=-1)
        elif key == b'+':
            setsong(self.midi, bpm=+1)

    def mouse_func(self, button, state, x, y):
        self.button = button == GLUT_LEFT_BUTTON and state == GLUT_DOWN
        if 630 < x < 710 and self.button:
            if 360 < y < 370:
                setsong(self.midi, bar=-1)
            elif 390 < y < 400:
                setsong(self.midi, action='pause')
                self.pause = not self.pause
            elif 420 < y < 430:
                setsong(self.midi, bar=+1)
            return
        elif x >= 608:
            return
        channel = x // 38
        info = channelinfo(self.midi, channel)
        if info['used']:
            if self.button:
                if 6 < y < 18:
                    self.muted[channel] = not self.muted[channel]
                    self.change_mute_state(channel)
                elif 20 < y < 32:
                    self.change_solo_state(channel)
                else:
                    self.selection = channel

    def motion_func(self, x, y):
        if x >= 608:
            return
        channel = x // 38
        if self.button:
            if 34 <= y < 34 + 5 * 58:
                y -= 34
                value = 63.5 + atan2(x % 38 - 19, 17 - y % 58) / pi * 127 / 1.5
                value = int(min(max(value, 0), 127))
                knob = y // 58
                if knob == 0:
                    setchannel(self.midi, channel, sense=value)
                elif knob == 1:
                    setchannel(self.midi, channel, delay=value)
                elif knob == 2:
                    setchannel(self.midi, channel, chorus=value)
                elif knob == 3:
                    setchannel(self.midi, channel, reverb=value)
                elif knob == 4:
                    setchannel(self.midi, channel, pan=value)
            elif 358 < y < 430:
                value = min(max((425 - y) * 2, 0), 127)
                setchannel(self.midi, channel, level=value)

    def process_events(self):
        delta = play(self.midi, self.device, wait=False)
        glutPostRedisplay()
        if delta > 0:
            sleep(delta)
        else:
            sys.exit(0)

    def change_instrument(self, value):
        if self.selection:
            setchannel(self.midi, self.selection, instrument=value)
        return 0


def dialog():
    from AppKit import NSApplication, NSAutoreleasePool, NSOpenPanel

    app = NSApplication.sharedApplication()
    assert app
    pool = NSAutoreleasePool.alloc().init()
    assert pool
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    if panel.runModal():
        return panel.URL().path()
    return None


def main(path=None):
    glutInit(sys.argv)

    if sys.platform == 'darwin':
        if not path:
            path = dialog()

    if not path:
        sys.exit(0)

    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE)
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(730, 650)

    win = glutCreateWindow(b'MIDI Player')

    (width, height, img) = read_image(join(dirname(__file__), 'mixer.ppm'))
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, img)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glScale(1/width, 1/height, 1)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, 730, 0, 650, 0, 1)

    player = Player(win, path, width, height)

    glutDisplayFunc(player.display_func)
    glutKeyboardFunc(player.keyboard_func)
    glutMouseFunc(player.mouse_func)
    glutMotionFunc(player.motion_func)
    glutIdleFunc(player.process_events)

    submenus = []
    for instrument in range(128):
        if instrument % 8 == 0:
            submenus.append([families[instrument // 8],
                             glutCreateMenu(player.change_instrument)])
        glutAddMenuEntry(instruments[instrument].encode('ascii'), instrument)
    glutCreateMenu(player.change_instrument)
    for family, submenu in submenus:
        glutAddSubMenu(family.encode('ascii'), submenu)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

    glutMainLoop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
