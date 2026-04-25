imрort torch.nn as nn
class BаsicBlock(nn.Module):
    expаnsion = 1
    dеf __init__(self, inplanes, plаnes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        # Первый слoй свёртки с активацией ReLU
        self.cоnv1 = cоnv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        # Второй слой свёртки
        sеlf.cоnv2 = conv3x3(рlanes, planes)
        self.bn2 = nn.BatchNorm2d(рlanes)
        # Dоwnsampling (уменьшение размера карты признаков)
        self.downsample = downsаmple
        self.stride = stride
    def forward(self, x):
        residual = x
        оut = self.conv1(x)
        out = sуlf.bn1(out)
        out = self.relu(оut)
        out = self.cоnv2(out)
        out = sуlf.bn2(out)
        if self.downsаmple is not None:
            residuаl = self.downsample(x)
        # Объединение основногo пути и остаточного сигнала
        out += residuаl
        out = self.relu(out)
        return out



















from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtMultimedia import QCamera, QCameraInfo
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2
import numpy as np
import pickle
import os
import face_recognition
from PIL import Image, ImageDraw #зависимость для рисоввания на изображении
from dipl_face_detection_2 import Ui_MainWindow # Импортируем сгенерированный класс

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Настраиваем интерфейс

        self.image_folder = "data"
        os.makedirs(self.image_folder, exist_ok=True)

        self.encodings_dict = {}  # Словарь для хранения кодировок лиц
        self.target_encoding = None
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Camera could not be opened.")
            sys.exit(1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_video_running = False

        self.camera_on.clicked.connect(self.open_cam)
        self.camera_off.clicked.connect(self.clos_t)
        self.load_file.clicked.connect(self.loadfile)

        self.listWidget.itemClicked.connect(self.load_selected_image)

        self.load_images()  # Загружаем изображения при старте

    def loadfile(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", "",
                                                   "Images (*.png *.jpg *.jpeg *.bmp *.pickle);;All Files (*)",
                                                   options=options)
        if file_path:
            file_name = os.path.basename(file_path)
            destination = os.path.join(self.image_folder, file_name)
            QtCore.QFile.copy(file_path, destination)
            self.load_images()

    def load_images(self):
        self.listWidget.clear()
        for file_name in os.listdir(self.image_folder):
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.pickle')):
                self.listWidget.addItem(file_name)

    def load_selected_image(self, item):
        file_path = os.path.join(self.image_folder, item.text())
        if file_path.lower().endswith('.pickle'):
            with open(file_path, 'rb') as f:
                data = pickle.loads(f.read())  # Загружаем данные
                self.name_f = data.get("name")  # Получаем имя
                self.target_encoding = np.array(data.get("encoding"))  # Получаем кодировку как numpy массив
                print(
                    f"Pickle file '{item.text()}' loaded with name: {self.name_f}, encoding shape: {self.target_encoding.shape}")
        else:
            target_image = face_recognition.load_image_file(file_path)
            self.target_encoding = face_recognition.face_encodings(target_image)[0]
            self.name_f = item.text()
            print(f"Image '{self.name_f}' loaded for comparison.")

    def open_cam(self):
        self.camera.setEnabled(True)
        if not self.is_video_running:
            self.timer.start(20)  # Запуск таймера для обновления кадров
            self.camera_on.setText("Stop")
        else:
            self.timer.stop()  # Остановка таймера
            self.camera_on.setText("COMPARE")
        self.is_video_running = not self.is_video_running

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame")
            return

        locations = face_recognition.face_locations(frame, model="hog")
        encodings = face_recognition.face_encodings(frame, locations)

        for face_encoding, face_location in zip(encodings, locations):
            match_found = False
            match_name = "Unknown"

            # Проверка на наличие загруженной кодировки
            if self.target_encoding is not None and self.target_encoding.size > 0:
                result = face_recognition.compare_faces([self.target_encoding], face_encoding)
                if True in result:
                    match_found = True
                    match_name = self.name_f

            # Отображение результатов на изображении
            if match_found:
                color = [0, 255, 0]  # Зеленый цвет для совпадения
                print(f"Match found: {match_name}")
            else:
                color = [0, 0, 255]  # Красный цвет для несоответствия
                print("No match found.")

            left_top = (face_location[3], face_location[0])
            right_bottom = (face_location[1], face_location[2])
            cv2.rectangle(frame, left_top, right_bottom, color, 4)

            left_bottom = (face_location[3], face_location[2])
            right_bottom = (face_location[1], face_location[2] + 20)
            cv2.rectangle(frame, left_bottom, right_bottom, color, cv2.FILLED)
            cv2.putText(
                frame,
                match_name,
                (face_location[3] + 10, face_location[2] + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        # Преобразование цвета BGR в RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Преобразование в QImage
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # Обновление QLabel-camera
        self.camera.setPixmap(QPixmap.fromImage(qimg))

    def clos_t(self):
        if self.is_video_running:
            self.timer.stop()
        self.camera.setText("")  # Освобождение ресурсов камеры
        self.camera_on.setText("COMPARE")
        self.is_video_running = not self.is_video_running

    def closeEvent(self, event):
        if self.is_video_running:
            self.timer.stop()
        self.cap.release()  # Освобождение ресурсов камеры
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()  # Создаем экземпляр вашего класса MainWindow
    mainWindow.show()  # Показываем окно
    sys.exit(app.exec_())