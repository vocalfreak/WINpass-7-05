from utils.image_utils import get_face_encodings_folders, real_time_recognition

# Paths
dataset_path = r"C:\Users\chiam\Downloads\winpass_training_set"
database_path = "winpass.db"

db_path = database_path 

#get_face_encodings_folders(dataset_path, db_path)
real_time_recognition(db_path)