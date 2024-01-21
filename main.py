import sys, os, cv2
import numpy as np
from range_slider import RangeSlider

from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QMainWindow, QLabel, QPushButton, QSlider

def generateSolidColorPixmap(w, h, color):
    canvas = QImage(QSize(w, h), QImage.Format_RGB30)
    for baris in range(0, h):
        for kolom in range(0, w):
            canvas.setPixel(kolom, baris, color.rgb())
    return canvas

class MainWindow(QMainWindow):
    selectedHue = 0
    selectedSaturation = 255
    selectedValue = 255

    lowerHSV = [0, 0, 0]
    upperHSV = [179, 255, 255]

    imgRaw = None
    imgMask = None
    imgMasked = None

    imgHsvSpace = None

    resized = QtCore.pyqtSignal()

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(
            __file__), "./assets/main_window.ui"), self)

        self.sliderH = self.findChild(RangeSlider, "sliderH")
        self.sliderS = self.findChild(RangeSlider, "sliderS")
        self.sliderV = self.findChild(RangeSlider, "sliderV")

        self.cboxHInverse = self.findChild(QCheckBox, "cboxHInverse")

        self.lblH = self.findChild(QLabel, "lblH")
        self.lblS = self.findChild(QLabel, "lblS")
        self.lblV = self.findChild(QLabel, "lblV")

        self.lblLower = self.findChild(QLabel, "lblLower")
        self.lblUpper = self.findChild(QLabel, "lblUpper")

        self.previewH = self.findChild(QLabel, "previewH")
        self.previewS = self.findChild(QLabel, "previewS")
        self.previewV = self.findChild(QLabel, "previewV")

        self.previewRaw = self.findChild(QLabel, "previewRaw")
        self.previewMask = self.findChild(QLabel, "previewMask")
        self.previewMaskedRaw = self.findChild(QLabel, "previewMaskedRaw")
        self.previewHsvSpace = self.findChild(QLabel, "previewHsvSpace")

        self.cboxErode = self.findChild(QCheckBox, "cboxErode")
        self.sliderErotion = self.findChild(QSlider, "sliderErotion")
        self.cboxDilate = self.findChild(QCheckBox, "cboxDilate")
        self.sliderDilation = self.findChild(QSlider, "sliderDilation")

        self.btnOpen = self.findChild(QPushButton, "btnOpen")
        self.btnCopy = self.findChild(QPushButton, "btnCopy")

        self.init_handler()
        self.loadHsvSpace()
        self.updateHSVPreview()

    def resizeEvent(self, event):
        self.resized.emit()
        return super(MainWindow, self).resizeEvent(event)

    def loadHsvSpace(self):
        self.imgHsvSpace = cv2.imread(os.path.join(os.path.dirname(__file__), "assets", "hsv_color.png"))
        
    def init_handler(self):
        self.resized.connect(self.onWindowsSizeChange)

        self.sliderH.sliderMoved.connect(self.onHChanged)
        self.sliderS.sliderMoved.connect(self.onSChanged)
        self.sliderV.sliderMoved.connect(self.onVChanged)
        self.btnOpen.clicked.connect(self.onBtnOpenClicked)
        self.btnCopy.clicked.connect(self.onBtnCopyClicked)

        self.cboxHInverse.stateChanged.connect(self.onCBoxHInverseChanged)
        self.cboxDilate.stateChanged.connect(self.updateMask)
        self.cboxErode.stateChanged.connect(self.updateMask)
        self.sliderErotion.valueChanged.connect(self.onSliderErodeChanged)
        self.sliderDilation.valueChanged.connect(self.onSliderDilateChanged)

    # =========== Helper ===========
    def inRange2(self, img):
        frame_HSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_orange = np.array(self.lowerHSV)
        upper_orange = np.array(self.upperHSV)

        if self.cboxHInverse.isChecked():
            ## collect H from 0 ~ lowerHSV
            lower_orange[0] = 0
            upper_orange[0] = self.lowerHSV[0]
            threshold_lower = cv2.inRange(
                frame_HSV, lower_orange, upper_orange)
            ## collect H from upperHSV ~ 255
            lower_orange[0] = self.upperHSV[0]
            upper_orange[0] = 255
            threshold_upper = cv2.inRange(
                frame_HSV, lower_orange, upper_orange)

            frame_threshold = cv2.bitwise_or(threshold_lower, threshold_upper)
        else:
            frame_threshold = cv2.inRange(
                frame_HSV, lower_orange, upper_orange)

        return frame_threshold

    def updateImageInLabel(self, label, _asQImage):
        w = label.size().width()
        h = label.size().height()
        label.setPixmap(QPixmap.fromImage(_asQImage).scaled(w, h, QtCore.Qt.KeepAspectRatio))
        # label.setPixmap(QPixmap.fromImage(_asQImage).scaledToWidth(label.size().width()))

    def updatePreviewHsvSpace(self):
        ## update the rainbow image on the lower left 
        if self.imgHsvSpace is None:
            return

        frame_threshold = self.inRange2(self.imgHsvSpace)

        frame_threshold = cv2.bitwise_and(self.imgHsvSpace, self.imgHsvSpace, mask=frame_threshold)
        _asQImage = QImage(
            frame_threshold.data, frame_threshold.shape[1], frame_threshold.shape[0], frame_threshold.shape[1]*3,  QtGui.QImage.Format_RGB888)
        _asQImage = _asQImage.rgbSwapped()
        self.previewHsvSpace.setPixmap(QPixmap.fromImage(_asQImage).scaledToWidth(self.previewMask.size().width()))

    def updateHSVPreview(self):
        prevH = generateSolidColorPixmap(
            200, 300, QColor.fromHsv(self.selectedHue, 255, 255))
        self.previewH.setPixmap(QPixmap.fromImage(prevH))

        prevS = generateSolidColorPixmap(
            200, 300, QColor.fromHsv(self.selectedHue, self.selectedSaturation, 255))
        self.previewS.setPixmap(QPixmap.fromImage(prevS))

        prevV = generateSolidColorPixmap(
            200, 300, QColor.fromHsv(self.selectedHue, self.selectedSaturation, self.selectedValue))
        self.previewV.setPixmap(QPixmap.fromImage(prevV))

        self.lblUpper.setText(
            f"H {self.upperHSV[0]}; S {self.upperHSV[1]}; V {self.upperHSV[2]}")
        self.lblLower.setText(
            f"H {self.lowerHSV[0]}; S {self.lowerHSV[1]}; V {self.lowerHSV[2]}")
        
        self.updateMask()
        self.updatePreviewHsvSpace() ## update the rainbow image on the lower left 

    def updateRawImg(self, img):
        self.imgRaw = img

        _imgAsQImg = QImage(
            self.imgRaw.data, self.imgRaw.shape[1], self.imgRaw.shape[0], QImage.Format_RGB888).rgbSwapped()

        # self.previewRaw.setPixmap(QPixmap.fromImage(
        #     _imgAsQImg).scaledToWidth(self.previewRaw.size().width()))
        self.updateImageInLabel(self.previewRaw, _imgAsQImg)

    def updateMask(self):
        if self.imgRaw is None:
            return

        frame_threshold = self.inRange2(self.imgRaw)

        if self.cboxErode.isChecked():
            _kernel = self.sliderErotion.value()
            frame_threshold = cv2.erode(frame_threshold, np.ones((_kernel, _kernel), dtype=np.uint8))
        
        if self.cboxDilate.isChecked():
            _kernel = self.sliderDilation.value()
            frame_threshold = cv2.dilate(frame_threshold, np.ones((_kernel, _kernel), dtype=np.uint8))

        self.updateMaskedRaw(frame_threshold)
        frame_threshold = cv2.cvtColor(frame_threshold, cv2.COLOR_GRAY2RGB)

        _asQImage = QImage(
            frame_threshold.data, frame_threshold.shape[1], frame_threshold.shape[0], frame_threshold.shape[1]*3,  QtGui.QImage.Format_RGB888)
        _asQImage = _asQImage.rgbSwapped()
        self.updateImageInLabel(self.previewMask, _asQImage)

    def updateMaskedRaw(self, masking):
        if self.imgRaw is None:
            return

        frame_threshold = cv2.bitwise_and(self.imgRaw, self.imgRaw, mask=masking)
        _asQImage = QImage(
            frame_threshold.data, frame_threshold.shape[1], frame_threshold.shape[0], frame_threshold.shape[1]*3,  QtGui.QImage.Format_RGB888)
        _asQImage = _asQImage.rgbSwapped()
        self.updateImageInLabel(self.previewMaskedRaw, _asQImage)

    # =========== EVENT HANDLER ===========
    def onWindowsSizeChange(self):
        if self.imgRaw is not None:
            self.updateRawImg(self.imgRaw)
        self.updateMask()
        self.updatePreviewHsvSpace()

    def onCBoxHInverseChanged(self):
        l = self.lowerHSV[0]
        h = self.upperHSV[0]
        if self.cboxHInverse.isChecked():
            self.lblH.setText(str(f"QT5 ({h*2},0,{l*2}) | cv2 ({h},0,{l})"))
        else:
            self.lblH.setText(str(f"QT5 ({l*2},{h*2}) | cv2 ({l},{h})"))
        self.updateHSVPreview()

    def onHChanged(self, low_value, high_value):
        self.lowerHSV[0] = low_value//2
        self.upperHSV[0] = high_value//2
        if self.cboxHInverse.isChecked():
            self.lblH.setText(str(f"QT5 ({high_value},0,{low_value}) | cv2 ({high_value//2},0,{low_value//2})"))
        else:
            self.lblH.setText(str(f"QT5 ({low_value},{high_value}) | cv2 ({low_value//2},{high_value//2})"))
        self.updateHSVPreview()

    def onSChanged(self, low_value, high_value):
        self.lowerHSV[1] = low_value
        self.upperHSV[1] = high_value
        self.lblS.setText(str(f"({low_value},{high_value})"))
        self.updateHSVPreview()

    def onVChanged(self, low_value, high_value):
        self.lowerHSV[2] = low_value
        self.upperHSV[2] = high_value
        self.lblV.setText(str(f"({low_value},{high_value})"))
        self.updateHSVPreview()

    def onSliderErodeChanged(self):
        self.cboxErode.setText(f"Erode {self.sliderErotion.value()}")
        self.updateMask()

    def onSliderDilateChanged(self):
        self.cboxDilate.setText(f"Dilate {self.sliderDilation.value()}")
        self.updateMask()

    def onBtnOpenClicked(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "QFileDialog.getOpenFileName()", "", "All Files (*);;Jpeg (*.jpeg);;BMP (*.bmp)", options=options)
        if not fileName:
            return
        # self.srcQimg = QImage(fileName=fileName, format=QImage.Format_RGB32)
        self.updateRawImg(cv2.imread(fileName))
        # with open(fileName, 'rb') as f:
        #     self.updateRawImg(QImage.fromData(f.read()))

    def onBtnCopyClicked(self):
        if self.cboxHInverse.isChecked():
            print("H:({},{})".format(self.upperHSV[0], self.lowerHSV[0]))
        else:
            print("H:({},{})".format(self.lowerHSV[0], self.upperHSV[0]))
        print("S: ({},{})\nV: ({},{})\n==========".format(self.lowerHSV[1], self.upperHSV[1], self.lowerHSV[2], self.upperHSV[2]))

if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
