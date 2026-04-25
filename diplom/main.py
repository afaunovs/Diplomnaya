import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QFileDialog, QListWidget
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtMultimedia import QCamera, QCameraInfo
from PyQt5.QtGui import QImage, QIcon, QPixmap
from PyQt5.QtCore import QTimer
import cv2
import numpy as np
import pickle
import os
import face_recognition
from PIL import Image, ImageDraw #зависимость для рисоввания на изображении
from dipl_face_detection_2 import Ui_MainWindow # Импортируем сгенерированный класс
from zastavka import GUi_MainWindow
#python -m PyQt5.uic.pyuic -x zastavka.ui -o zastavka.py


class GMainWindow(QMainWindow, GUi_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) # Настраиваем интерфейс

        self.play.clicked.connect(self.perehod_okna)

    def perehod_okna(self):

        self.mainWindow = MainWindow()  # Создаем экземпляр вашего класса MainWindow
        self.mainWindow.show()  # Показываем окно
        self.close()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self) # Настраиваем интерфейс

        self.image_folder = "data"
        os.makedirs(self.image_folder, exist_ok=True)

        # Проверка наличия файла с кодировками
        #if not os.path.exists(""):
         #   print("Encoding file not found!")
          #  sys.exit(1)

        #with open("my_face_encodings.pickle", "rb") as f:
         #   self.data = pickle.load(f)
        #self.target_image = face_recognition.load_image_file("target_image.jpg")
        #self.target_encoding = face_recognition.face_encodings(self.target_image)[0]


        self.target_encoding = None
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Camera could not be opened.")
            sys.exit(1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_video_running = False

        self.image_filename = None

        self.camera_on.clicked.connect(self.open_cam)
        self.camera_off.clicked.connect(self.clos_t)
        self.load_file.clicked.connect(self.loadfile)
        self.pushButton_label.clicked.connect(self.image_file)

        self.listWidget.itemClicked.connect(self.load_selected_image)

        self.load_images()

    def image_file(self):
        if self.pushButton_label.text() != "CLEAR":# проверяется на нажатие кнопки
            options = QFileDialog.Options() #открытие диалогового окна
            file_path, _ = QFileDialog.getOpenFileName(self, "Select an File", "",
                                                       "Images (*.png *.jpg *.jpeg *.bmp *.pickle);;All Files (*)",
                                                       options=options)#указывается путь загрузки
            if file_path:#условие в случае выбора файла
                file_name = os.path.basename(file_path)#копирование имени файла
                self.label_image.setPixmap(QtGui.QPixmap(file_path))#присвоение и изменение избражения к label
                self.label_image.setScaledContents(True)#растянуть по контуру элеммента
                self.image_filename = file_path
                self.pushButton_label.setText('CLEAR')

        else:
            self.label_image.clear()#при повторном нажати удаляется изборажение
            self.pushButton_label.setText('Load_image')#и надпись меняется обратно



    def loadfile(self):#загрука файлов в список данных
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an File", "",
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
                self.data = pickle.load(f)
                self.name_f = item.text()
            print("Pickle file loaded.")
        else:
            target_image = face_recognition.load_image_file(file_path)
            self.target_encoding = face_recognition.face_encodings(target_image)[0]
            self.name_f = item.text()
            print("Image loadervfor comparison")


    def open_cam(self):#запуск основной процедуры
        self.camera.setEnabled(True)
        if not self.is_video_running:#проверяется на включени видео потока
            self.timer.start(20)  # Запуск таймера для обновления кадров
            self.camera_on.setText("Stop")
        else:
            self.timer.stop()  # Остановка таймера
            self.camera_on.setText("COMPARE")
        self.is_video_running = not self.is_video_running

    def update_frame(self):
        if self.label_image.pixmap() is not None:
            pixmap = self.label_image.pixmap()  # Получаем QPixmap
            image = pixmap.toImage()
            # Преобразовать QImage в формат, который может быть обработан OpenCV
            # Нам нужно преобразовать в RGBA, если оно в этом формате
            image = image.convertToFormat(4)  # 4 = Изображение::Format_ARGB32
            width = image.width()
            height = image.height()

            ptr = image.bits()
            ptr.setsize(image.byteCount())
            # Создайте массив NumPy на основе изображения
            cv_image = np.array(ptr).reshape((height, width, 4))  # на 4 канала
            cv_image = cv_image[:, :, :3]  #Отказываемся от альфа-канала
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGBA2BGR)  # OpenCV использует BGR
            frame = cv_image
            ret = True

            #return ret, frame

        else:
            ret, frame = self.cap.read()
        if not ret: # or frame is None:  # Проверка на успешность захвата фрейма
            print("Failed to capture frame")
            return  # Выход, если не удалось захватить фрейм
        locations = face_recognition.face_locations(frame, model="hog")
        encodings = face_recognition.face_encodings(frame, locations)

        for face_encoding, face_location in zip(encodings, locations):
            if self.target_encoding is not None:
                result = face_recognition.compare_faces([self.target_encoding], face_encoding)
                match = None

                if True in result:
                    match = self.name_f#"!!!!!"
                    color = [0, 255, 0]
                    print(f"Match found! {match}")
                else:
                    match = "NOT DECODe"
                    color = [0, 0, 255]
                    print("ACHTUNG! ALARM!")

                left_top = (face_location[3], face_location[0])
                right_bottom = (face_location[1], face_location[2])
                cv2.rectangle(frame, left_top, right_bottom, color, 4)

                left_bottom = (face_location[3], face_location[2])
                right_bottom = (face_location[1], face_location[2] + 20)
                cv2.rectangle(frame,left_bottom,right_bottom, color, cv2.FILLED)
                cv2.putText(
                    frame,
                    match,
                    (face_location[3] + 10, face_location[2] + 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    4
                )
            else:
                '''result = face_recognition.face_locations(frame)
                pil_result = Image.fromarray(result)
                draw_face =ImageDraw.Draw(pil_result)
                for(top, right, bottom, left) in result:
                    draw_face.rectangle(((left, top), (right, bottom)), outline=(255, 255, 0), width=4)
                del draw_face'''
                left_top = (face_location[3], face_location[0])
                right_bottom = (face_location[1], face_location[2])
                cv2.rectangle(frame, left_top, right_bottom, [0, 255, 255], 4)

                left_bottom = (face_location[3], face_location[2])
                right_bottom = (face_location[1], face_location[2] + 50)
                cv2.rectangle(frame,left_bottom,right_bottom, [0, 255, 255], cv2.FILLED)
                '''cv2.putText(
                    frame,
                    "unknown person",
                    (face_location[3] + 10, face_location[2] + 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    4
                )'''
                # Определяем текст и разбиваем его на слова
                text = "unknown person"
                words = text.split()

                # Начальная позиция для текста
                x = face_location[3] + 10  # X-координата
                y = face_location[2] + 15  # Начальная Y-координата

                for word in words:
                    cv2.putText(
                        frame,
                        word,
                        (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 255),
                        4
                    )
                    y += 30  # Увеличиваем Y-координату для следующего слова (можно настроить отступ)


            # Преобразование цвета BGR в RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Преобразование в QImage
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # Обновление QLabel-camera
            self.camera.setPixmap(QPixmap.fromImage(qimg))
            self.camera.setScaledContents(True)

        return ret, frame

    def clos_t(self):#
        if self.is_video_running:
            self.timer.stop()
        self.cap.release()  # Освобождение ресурсов камеры
        self.camera_on.setText("COMPARE")
        self.is_video_running = not self.is_video_running

    def closeEvent(self, event):
        if self.is_video_running:
            self.timer.stop()
        self.cap.release()  # Освобождение ресурсов камеры
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = GMainWindow()  # Создаем экземпляр вашего класса MainWindow
    mainWindow.show()  # Показываем окно
    sys.exit(app.exec_())