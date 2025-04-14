import os
from PIL import Image, ImageOps
import face_recognition as fr
import cv2 
import sqlite3
import numpy as np

def resize_with_padding(img_path, size=(250, 250), fill_color=(0, 0, 0)):
    img = Image.open(img_path)
    img.thumbnail(size, Image.LANCZOS)
    delta_w = size[0] - img.size[0]
    delta_h = size[1] - img.size[1]
    padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)
    return ImageOps.expand(img, padding, fill=fill_color)

def get_face_encodings(img_path):
    img = cv2.imread(img_path)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_encoding = fr.face_encodings(rgb_img)
    return img_encoding[0] if img_encoding else None






