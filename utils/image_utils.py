import os
from PIL import Image, ImageOps

def resize_with_padding(img_path, size=(250, 250), fill_color=(0, 0, 0)):
    img = Image.open(img_path)
    img.thumbnail(size, Image.LANCZOS)
    delta_w = size[0] - img.size[0]
    delta_h = size[1] - img.size[1]
    padding = (delta_w // 2, delta_h // 2, delta_w - delta_w // 2, delta_h - delta_h // 2)
    return ImageOps.expand(img, padding, fill=fill_color)

#source_root = r"C:\Users\chiam\Downloads\pictures"
#output_root = r"C:\Users\chiam\Downloads\pictures_resized"  

#os.makedirs(output_root, exist_ok=True)

#for person in os.listdir(source_root):
#    person_path = os.path.join(source_root, person)
#    if not os.path.isdir(person_path):
#        continue
#
#    output_person_path = os.path.join(output_root, person)
#    os.makedirs(output_person_path, exist_ok=True)
#
#    for image_name in os.listdir(person_path):
#        image_path = os.path.join(person_path, image_name)
#
#        try:
#            padded_img = resize_with_padding(image_path)
#            padded_img.save(os.path.join(output_person_path, image_name))
#            print(f"Processed: {person}/{image_name}")
#        except Exception as e:
#            print(f"Failed: {person}/{image_name} - {e}")
