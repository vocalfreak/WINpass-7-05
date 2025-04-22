import cv2
import os

folder_name = "pictures"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

cam = cv2.VideoCapture(0)

cv2.namedWindow("Photobooth")

img_counter = 0

while True:
    ret,frame = cam.read()

    if not ret:
        print("Failed to grab the frame")
        break

    cv2.imshow("Photobooth",frame)


    k=cv2.waitKey(1)

    if k%256 == 27:
        print("Escape hit, closing the app")
        break
    
    elif k%256 == 32:
        img_name = os.path.join(folder_name,"opencv_frame_{}.png".format(img_counter))
        cv2.imwrite(img_name,frame)
        print("Photo taken")
        img_counter+=1

cam.release()

cv2.destroyAllWindows()