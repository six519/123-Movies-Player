#!/usr/bin/env python
import sys
import os
import re

try:
    from localsettings import *
except:
    pass

import vlc
from PyQt4 import QtCore, QtGui 
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

PLAYER_DEFAULT_WIDTH = 800
PLAYER_DEFAULT_HEIGHT = 600
PLAYER_VOLUME_MAX_SLIDER = 100
PLAYER_STATUSBAR_TIMEOUT = 5000
PLAYER_MOVIE_BASE_URL = "http://123movies.to/film/"

class OneTwoThreePlayer(QtGui.QMainWindow):

    def __init__(self, *args, **kwargs):
        self.qtApp = QtGui.QApplication([])
        super(QtGui.QMainWindow, self).__init__(*args, **kwargs)

        self.vlcInstance = vlc.Instance()
        self.vlcMediaPlayer = self.vlcInstance.media_player_new()
        self.isFullScreen = False
        self.currentMRL = ""
        self.subtitleFile = ""
        self.initUI()
        self.originalBackground = self.palette().color(self.backgroundRole())

    def initUI(self):
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("123 Movies Player")
        self.widget = QtGui.QWidget(self)
        self.setCentralWidget(self.widget)
        self.clickSound = QtGui.QSound("resources/push.wav")

        #create controls
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar(self.statusBar)

        self.mrlLineEdit = QtGui.QLineEdit()

        self.loadButton = QtGui.QPushButton()
        self.loadButton.setIcon(QtGui.QIcon("resources/down.png"))
        self.loadButton.setToolTip("Load movie")
        self.connect(self.loadButton, QtCore.SIGNAL("clicked()"), self.loadVideo)

        self.loadSubtitle = QtGui.QPushButton()
        self.loadSubtitle.setIcon(QtGui.QIcon("resources/Text-32.png"))
        self.loadSubtitle.setToolTip("Load subtitle")
        self.connect(self.loadSubtitle, QtCore.SIGNAL("clicked()"), self.loadSubtitleFile)

        self.fullScreenButton = QtGui.QPushButton()
        self.fullScreenButton.setIcon(QtGui.QIcon("resources/fullscreen.png"))
        self.fullScreenButton.setToolTip("Fullscreen mode")
        self.connect(self.fullScreenButton, QtCore.SIGNAL("clicked()"), self.setFullscreen)

        self.volumeSlider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.volumeSlider.setMaximum(PLAYER_VOLUME_MAX_SLIDER)
        self.volumeSlider.setValue(self.vlcMediaPlayer.audio_get_volume())
        self.volumeSlider.setToolTip("Adjust volume")
        self.connect(self.volumeSlider, QtCore.SIGNAL("valueChanged(int)"), self.changeVolume)
        
        self.videoFrame = QtGui.QFrame()
        self.videoFramePalette = self.videoFrame.palette()
        #set the background color to light sky blue
        self.videoFramePalette.setColor(QtGui.QPalette.Window, QtGui.QColor(135, 206, 250))
        self.videoFrame.setPalette(self.videoFramePalette)
        self.videoFrame.setAutoFillBackground(True)

        self.hBoxLayout = QtGui.QHBoxLayout()
        self.hBoxLayout.addWidget(self.volumeSlider)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.loadButton)
        self.hBoxLayout.addWidget(self.loadSubtitle)
        self.hBoxLayout.addWidget(self.fullScreenButton)

        self.vBoxLayout = QtGui.QVBoxLayout()
        #add controls to layout
        self.vBoxLayout.addWidget(self.mrlLineEdit)
        self.vBoxLayout.addWidget(self.videoFrame)
        self.vBoxLayout.addLayout(self.hBoxLayout)

        self.widget.setLayout(self.vBoxLayout)
        self.resize(PLAYER_DEFAULT_WIDTH, PLAYER_DEFAULT_HEIGHT)
        
        self.layoutMargins = self.vBoxLayout.getContentsMargins()

    def show(self):
        super(QtGui.QMainWindow, self).show()
        self.qtApp.exec_()

    def loadVideo(self):

        self.mrlLineEdit.setEnabled(False)
        self.clickSound.play()
        self.statusBar.showMessage("loading information from %s" % self.mrlLineEdit.text(), PLAYER_STATUSBAR_TIMEOUT)
        self.loadButton.setEnabled(False)

        if re.search("^(%s).+" % PLAYER_MOVIE_BASE_URL, self.mrlLineEdit.text()):
            
            wdriver = webdriver.Chrome("./resources/chromedriver")
            wdriver.set_window_size(0, 0)
            wdriver.set_window_position(self.x(), self.y())
            wdriver.get("%swatching.html" % str(self.mrlLineEdit.text()))

            videoLink = WebDriverWait(wdriver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )

            self.currentMRL = videoLink.get_attribute("src")
            print self.currentMRL
            
            wdriver.quit()

            media = self.vlcInstance.media_new(self.currentMRL)
            self.vlcMediaPlayer.set_media(media)
            self.vlcMediaPlayer.set_nsobject(self.videoFrame.winId())
            self.vlcMediaPlayer.play()
            if self.subtitleFile:
                self.vlcMediaPlayer.video_set_subtitle_file(str(self.subtitleFile))
            self.statusBar.showMessage("playing video... please wait...", PLAYER_STATUSBAR_TIMEOUT)
        else:
            self.statusBar.showMessage("Invalid URL!", PLAYER_STATUSBAR_TIMEOUT)
            
            self.mrlLineEdit.setEnabled(True)
            self.mrlLineEdit.setText("")

        self.loadButton.setEnabled(True)   
    
    def loadSubtitleFile(self):
        self.clickSound.play()

        subtitleFile = QtGui.QFileDialog.getOpenFileName(self, "Open .srt File", os.path.expanduser('~'))

        if str(subtitleFile) != "":
            self.subtitleFile = subtitleFile
            self.statusBar.showMessage("%s subtitle loaded..." % os.path.basename(str(self.subtitleFile)), PLAYER_STATUSBAR_TIMEOUT)

            if self.vlcMediaPlayer.is_playing():
                self.vlcMediaPlayer.video_set_subtitle_file(str(self.subtitleFile))
    
    def changeVolume(self, vol):
        self.statusBar.showMessage("adjusting volume to %s" % vol, PLAYER_STATUSBAR_TIMEOUT)
        self.vlcMediaPlayer.audio_set_volume(vol)

    def setFullscreen(self):
        
        thisPalette = self.palette()
        thisPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(0,0,0))
        self.setPalette(thisPalette)

        self.clickSound.play()
        self.mrlLineEdit.setVisible(False)
        self.volumeSlider.setVisible(False)
        self.loadButton.setVisible(False)
        self.loadSubtitle.setVisible(False)
        self.fullScreenButton.setVisible(False)
        self.statusBar.setVisible(False)
        self.showFullScreen()
        self.setCursor(QtCore.Qt.BlankCursor)
        self.isFullScreen = True
        self.vBoxLayout.setContentsMargins(0,0,0,0)

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Escape and self.isFullScreen:

            thisPalette = self.palette()
            thisPalette.setColor(QtGui.QPalette.Window, self.originalBackground)
            self.setPalette(thisPalette)

            self.mrlLineEdit.setVisible(True)
            self.volumeSlider.setVisible(True)
            self.loadButton.setVisible(True)
            self.loadSubtitle.setVisible(True)
            self.fullScreenButton.setVisible(True)
            self.statusBar.setVisible(True)
            self.resize(PLAYER_DEFAULT_WIDTH, PLAYER_DEFAULT_HEIGHT)
            self.showNormal()
            self.isFullScreen = False
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.vBoxLayout.setContentsMargins(self.layoutMargins[0],self.layoutMargins[1],self.layoutMargins[2],self.layoutMargins[3])
            self.statusBar.showMessage("exits to fullscreen mode...", PLAYER_STATUSBAR_TIMEOUT)

if __name__ == "__main__":
    player = OneTwoThreePlayer()
    player.show()