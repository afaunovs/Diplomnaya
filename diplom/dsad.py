import face_recognition
from PIL import Image, ImageDraw
import pickle
import cv2
#import bot

def detect_person_in_video():
    data = pickle.loads(open("regina_encodings.pickle", "rb").read())
    print(data)

def main():
    detect_person_in_video()

if __name__ == '__main__':
    main()
