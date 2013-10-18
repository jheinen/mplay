#!/usr/bin/env python

import sys
import os
from math import sin, cos, atan2, pi
from time import sleep, time

from OpenGL.GLUT import glutAddMenuEntry, glutAddSubMenu, glutAttachMenu, \
    glutCreateMenu,glutCreateWindow, glutDisplayFunc, glutIdleFunc, glutInit, \
    glutInitDisplayMode, glutInitWindowPosition, glutInitWindowSize, \
    glutKeyboardFunc, glutMainLoop, glutMotionFunc, glutMouseFunc, \
    glutSwapBuffers, GLUT_DOUBLE, GLUT_DOWN, GLUT_LEFT_BUTTON, GLUT_RGB, \
    GLUT_RIGHT_BUTTON
from OpenGL.GL import glBegin, glClear, glColor3f, glColor4f, glDrawPixels, \
    glEnd, glLoadIdentity, glMatrixMode, glOrtho, glPixelStorei, glVertex2f, \
    GL_COLOR_BUFFER_BIT, GL_LINES, GL_MODELVIEW, GL_NEAREST, GL_PROJECTION, \
    GL_QUADS, GL_RGB, GL_UNPACK_ALIGNMENT, GL_UNSIGNED_BYTE
from OpenGL.GL.EXT.framebuffer_object import glBindFramebufferEXT, \
    glBindRenderbufferEXT, glGenFramebuffersEXT, glGenRenderbuffersEXT, \
    glFramebufferRenderbufferEXT, glRenderbufferStorageEXT, \
    GL_COLOR_ATTACHMENT0_EXT, GL_RENDERBUFFER_EXT
from OpenGL.GL.EXT.framebuffer_blit import glBlitFramebufferEXT, \
    GL_DRAW_FRAMEBUFFER_EXT, GL_READ_FRAMEBUFFER_EXT

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


def Image(path):
    f = open(path, 'rb')
    f.readline()  # magic number
    width, height = map(int, f.readline().split())
    f.readline()  # number of colors
    img = f.read(width * height * 3)
    f.close()
    if sys.platform == 'darwin':
        img = b''.join(reversed([row for row in chunks(img, width * 3)]))
    return width, height, img


def CopyPixels(tox, toy, w, h, fromx, fromy):
    if sys.platform != 'darwin':
        fromy = 650 - (fromy + h)
    glBlitFramebufferEXT(fromx, fromy, fromx + w, fromy + h,
                         tox, toy, tox + w, toy + h,
                         GL_COLOR_BUFFER_BIT, GL_NEAREST)


def DrawText(x, y, s, color=0):
    for c in s:
        row = ord(c) // 16
        if ord(c) > 127:
            row -= 2
        fromx, fromy = (ord(c) % 16 * 7 + 770, 424 - row * 14)
        fromy += [0, -168, 168][color]
        if sys.platform != 'darwin':
            fromy = 650 - (fromy + 12)
        glBlitFramebufferEXT(fromx, fromy, fromx + 7, fromy + 12,
                             x, y, x + 7, y + 12,
                             GL_COLOR_BUFFER_BIT, GL_NEAREST)
        x += 7


def DrawLine(x1, y1, x2, y2):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, 730, 0, 650, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()


def PaintKnob(centerx, centery, value):
    angle = pi * (value - 64) / 64 * 0.75
    x, y = (centerx + 9 * sin(angle), centery + 9 * cos(angle))
    glColor3f(1, 1, 1)
    DrawLine(centerx, centery + 9, x, y + 9)


def DrawRect(x, y, width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, 730, 0, 650, 0, 1)
    glMatrixMode(GL_MODELVIEW)
    glColor4f(0.71, 0.83, 1, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()


def PaintNotes(notes):
    key = (2, 10, 20, 33, 39, 57, 66, 76, 86, 94, 107, 113)
    for note in notes:
        x = 312 + key[note % 12]
        if (note % 12) in [1, 3, 6, 8, 10]:
            DrawRect(x, 48, 7, 24)
        else:
            DrawRect(x, 14, 10, 24)


class Player():
    def __init__(self, win, path, width, height):
        self.win = win
        self.midi = read(path)
        self.device = midiDevice()
        self.muted = 16 * [False]
        self.solo = 16 * [False]
        self.last_update = 0
        self.width = width
        self.height = height
        self.button = False
        self.selection = None
        self.pause = False

    def update(self):
        glBlitFramebufferEXT(0, 0, 730, 650, 0, 0, 730, 650,
                             GL_COLOR_BUFFER_BIT, GL_NEAREST)
        for channel in range(16):
            color = 0 if channel != self.selection else 2
            info = channelinfo(self.midi, channel)
            x = 10 + channel * 38
            if info['used']:
                name = info['name'] if channel != 9 else 'Drums'
                DrawText(620, 562 - channel * 14, name, color)
                if self.muted[channel]:
                    CopyPixels(x - 6, 633, 31, 11, 735, 633)
                if self.solo[channel]:
                    CopyPixels(x - 6, 619, 31, 10, 735, 619)
            PaintKnob(x + 9, 581, info['sense'])
            DrawText(x, 559, '%3d' % info['sense'], color)
            PaintKnob(x + 9, 523, info['delay'])
            DrawText(x, 501, '%3d' % info['delay'], color)
            PaintKnob(x + 9, 465, info['chorus'])
            DrawText(x, 443, '%3d' % info['chorus'], color)
            PaintKnob(x + 9, 407, info['reverb'])
            DrawText(x, 386, '%3d' % info['reverb'], color)
            pan = info['pan']
            PaintKnob(x + 9, 349, pan)
            lr = 'L R'[(pan > 64) - (pan < 64) + 1]
            DrawText(x, 327, '%s%2d' % (lr, abs(pan - 64)), color)
            if info['used']:
                DrawText(x, 310, '%3d' % info['instrument'], color)
                DrawText(x - 5, 295, '%2d' % info['variation'], color)
                DrawText(x, 204, '%3d' % info['level'], color)
                CopyPixels(x + 13, 295, 12, 15, 754, 295)
                level = info['level']
            else:
                level = 0
            CopyPixels(x - 6, 204, 12, 91, 4, 204)
            CopyPixels(x - 6, 219 + level // 2, 12, 11, 735, 225)
            CopyPixels(x + 13, 219, 12, info['intensity'] // 2, 754, 219)
            if info['intensity'] >= 4:
                info['intensity'] -= 4
            else:
                info['intensity'] = 0

        DrawText(15, 177, fileinfo(self.midi))
        DrawText(15, 162, songinfo(self.midi))
        DrawText(15, 142, lyrics(self.midi), 1)
        chord, notes = chordinfo(self.midi)
        DrawText(15, 120, chord)
        PaintNotes(notes)
        ticker = '            Python MIDI Player  \xa8 2013 by Josef Heinen '
        beat = beatinfo(self.midi)
        shift = beat % len(ticker.strip()) + 1
        if shift + 12 < len(ticker):
            DrawText(630, 628, ticker[shift: shift + 12])
        for led in range(4):
            if beat % 4 == led:
                CopyPixels(632 + led * 20, 309, 16, 30, 770, 585)
        if self.pause:
            CopyPixels(665, 251, 10, 10, 850, 604)
        else:
            CopyPixels(665, 251, 10, 10, 860, 604)

    def changeMuteState(self, channel):
        setchannel(self.midi, channel, muted=self.muted[channel])

    def changeSoloState(self, channel):
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

    def Display(self):
        self.update()
        glutSwapBuffers()

    def Key(self, key, x, y):
        if key == b'\x1b':
            setsong(self.midi, action='exit')
            sys.exit(0)
        elif key == b'\t':
            if self.selection != None:
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
            self.changeMuteState(channel)
        elif key == b'a':
            for channel in range(16):
                self.muted[channel] = self.solo[channel] = False
                self.changeMuteState(channel)
        elif key == b'd':
            self.muted[9] = not self.muted[9]
            self.changeMuteState(9)
        elif key == b'D':
            self.changeSoloState(9)
        elif key in MUTE_ON_OFF:
            for channel in range(16):
                info = channelinfo(self.midi, channel)
                if channel != 9 and info['family'] in MUTE_ON_OFF[key]:
                    self.muted[channel] = not self.muted[channel]
                self.changeMuteState(channel)
        elif key in SOLO_ON:
            for channel in range(16):
                info = channelinfo(self.midi, channel)
                if channel != 9 and info['family'] in SOLO_ON[key]:
                    self.muted[channel] = False
                else:
                    self.muted[channel] = True
                    self.solo[channel] = False
                self.changeMuteState(channel)
        elif key == b'<':
            setsong(self.midi, shift=-1)
        elif key == b'>':
            setsong(self.midi, shift=+1)
        elif key == b'-':
            setsong(self.midi, bpm=-1)
        elif key == b'+':
            setsong(self.midi, bpm=+1)

    def Mouse(self, button, state, x, y):
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
                    self.changeMuteState(channel)
                elif 20 < y < 32:
                    self.changeSoloState(channel)
                else:
                    self.selection = channel

    def Motion(self, x, y):
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

    def processEvents(self):
        delta = play(self.midi, self.device, wait=False)
        if time() - self.last_update > 0.04:
            self.Display()
            self.last_update = time()
        if delta > 0.02:
            delta = 0.02
        elif delta == 0:
            sys.exit(0)
        sleep(delta)

    def changeInstrument(self, value):
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


def top():
    try:
        stderr = os.dup(sys.stderr.fileno())
        fd = os.open('/tmp/mplay.log', os.O_CREAT | os.O_WRONLY)
        os.dup2(fd, sys.stderr.fileno())
        from AppKit import NSApplication

        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(1)
        os.dup2(stderr, sys.stderr.fileno())
    except BaseException:
        pass


def main():
    glutInit(sys.argv)

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = None
    if sys.platform == 'darwin':
        top()
        if not path:
            path = dialog()

    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE)
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(730, 650)

    win = glutCreateWindow(b'MIDI Player')

    (width, height, img) = Image('mixer.ppm')
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    rbo = glGenRenderbuffersEXT(1)
    glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, rbo)
    glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT, GL_RGB, width, height)

    fbo = glGenFramebuffersEXT(1)
    glBindFramebufferEXT(GL_READ_FRAMEBUFFER_EXT, fbo)
    glFramebufferRenderbufferEXT(GL_READ_FRAMEBUFFER_EXT,
                                 GL_COLOR_ATTACHMENT0_EXT,
                                 GL_RENDERBUFFER_EXT, rbo)

    glBindFramebufferEXT(GL_DRAW_FRAMEBUFFER_EXT, fbo)
    glClear(GL_COLOR_BUFFER_BIT)
    glDrawPixels(width, height, GL_RGB, GL_UNSIGNED_BYTE, img)
    glBindFramebufferEXT(GL_DRAW_FRAMEBUFFER_EXT, 0)

    player = Player(win, path, width, height)

    glutDisplayFunc(player.Display)
    glutKeyboardFunc(player.Key)
    glutMouseFunc(player.Mouse)
    glutMotionFunc(player.Motion)
    glutIdleFunc(player.processEvents)

    submenus = []
    for instrument in range(128):
        if instrument % 8 == 0:
            submenus.append([families[instrument // 8],
                             glutCreateMenu(player.changeInstrument)])
        glutAddMenuEntry(instruments[instrument].encode('ascii'), instrument)
    glutCreateMenu(player.changeInstrument)
    for family, submenu in submenus:
        glutAddSubMenu(family.encode('ascii'), submenu)
    glutAttachMenu(GLUT_RIGHT_BUTTON)

    glutMainLoop()


if __name__ == "__main__":
    main()
