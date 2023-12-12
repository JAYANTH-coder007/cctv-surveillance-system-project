import face_recognition.api as face_recognition
import cv2, pickle, os, csv, stat
import numpy as np
from datetime import datetime
from datetime import date
import matplotlib.pyplot as plt
import matplotlib as mpl
from imutils import face_utils
import pymysql
import dlib
p = "shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(p)

def dbConnection():
    try:
        connection = pymysql.connect(host="localhost", user="root", password="root", database="cctv",port=3307)
        return connection
    except:
        print("Something went wrong in database Connection")

def dbClose():
    try:
        dbConnection().close()
    except:
        print("Something went wrong in Close DB Connection")
        
con = dbConnection()
cursor = con.cursor()

def mark_your_attendance():
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create a video file name using the timestamp
    video_filename = f"static/cam_videos/video_{timestamp}.avi"
    video_name = f"video_{timestamp}.avi"

    mpl.rcParams['toolbar'] = 'None'
    STORAGE_PATH = "storage"

    try:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(video_filename, fourcc, 20.0, (640, 480))  # Adjust frame size (640, 480) and frame rate (20.0) as needed

        with open( os.path.join(STORAGE_PATH, "known_face_ids.pickle"),"rb") as fp:
            known_face_ids = pickle.load(fp)
        with open( os.path.join(STORAGE_PATH, "known_face_encodings.pickle"),"rb") as fp:
            known_face_encodings = pickle.load(fp)
    except:
        known_face_encodings = []
        known_face_ids = []

    name = "Unknown"
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    sanity_count = 0
    unknown_count = 0
    marked = True
    
    try:
        video_capture = cv2.VideoCapture(0+ cv2.CAP_DSHOW)
        ret, frame = video_capture.read()
    
        studentname=''
        while True:
            # Grab a single frame of video
            ret, frame = video_capture.read()
            # print("FRAME READ WORKS")
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
    
            # Only process every other frame of video to save time
            if process_this_frame:
                # Find all the faces and face encodings in the current frame of video
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  
                # detect faces in the grayscale image
                rects = detector(gray, 0)
                
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    
                face_names = []
                for face_encoding in face_encodings:
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance = 0.35)
                    name = "Unknown"
    
                    # # If a match was found in known_face_encodings, just use the first one.
                    # if True in matches:
                    #     first_match_index = matches.index(True)
                    #     name = known_face_ids[first_match_index]
    
                    # Or instead, use the known face with the smallest distance to the new face
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    # print(face_distances)
                    try:
                        best_match_index = np.argmin(face_distances)
                        marked = True
                        print("Students have been marked")
                    except:
                        print("No students have been marked")
                        # video_capture.release()
                        # cv2.destroyAllWindows()
                        marked = False
                        return marked
                    if matches[best_match_index]:
                        name = known_face_ids[best_match_index]
    
                    face_names.append(name)
            
            
            if(name == "Unknown"):
                unknown_count += 1
            else:
                unknown_count = 0
    
            if(unknown_count == 400):
                # video_capture.release()
                # cv2.destroyAllWindows()
                print("You haven't been registered")
                marked = False
                unknown_count = 0
                break
    
            process_this_frame = not process_this_frame
    
    
            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
    
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
    
                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.7, (255, 255, 255), 1)
    
            cv2.imshow('Video', frame)
            out.write(frame)
            
            if cv2.waitKey(20) == 27:
                break
    
            # plt.ion()
            # im1.set_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            # plt.pause(0.001)
            # # as opencv loads in BGR format by default, we want to show it in RGB.
            # plt.show()
    
            # print("AFTER SHOWING")
            # Hit 'q' on the keyboard to quit!
            if(sanity_count == 0):
                prev_name = name
                sanity_count += 1
    
            elif(sanity_count < 60):
                if(prev_name == name and name != "Unknown"):
                    sanity_count += 1
                    prev_name = name
                else:
                    sanity_count = 0
    
            elif(sanity_count == 60):
                # print("Face registered")
                # video_capture.release()
                # cv2.destroyAllWindows()
                sanity_count = 0
                now1 = datetime.now()
                dt_string = now1.strftime("%d/%m/%Y %H:%M:%S")
                date1 = dt_string.split(" ")[0]
                time = dt_string.split(" ")[1]
                studentname=str(name)#+" at "+str(date)
                #writer.writerow([name, date, time])
                # print(name + date + time)
                break
    
        # Release handle to the webcam
    
        out.release()
        today = date.today()
        current_time = datetime.now().strftime("%H:%M")
        
        sql = "INSERT INTO videodetails(videoname,videopath,date,time) VALUES (%s, %s, %s, %s)"
        val = (video_name,video_filename, str(today), str(current_time))
        cursor.execute(sql, val)
        con.commit()
        
        # plt.close()
        video_capture.release()
        cv2.destroyAllWindows()
        studentname = face_names[0]
        dt = date1+" "+time
        print("printing face_names")
        print(studentname)
        print(marked)
        return marked,studentname,dt
    except Exception as e:
        print(e)
        return False,"",""


# mark_your_attendance()
