import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np
from datetime import datetime

# Initialize Firebase app
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-5afa0-default-rtdb.firebaseio.com/",
    'storageBucket': "faceattendancerealtime-5afa0.appspot.com/images"
})

# Get storage bucket reference
bucket = storage.bucket()

# Initialize video capture
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Load background image
imgBackground = cv2.imread('Resources/background.png')

# Load mode images
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Load encoding data
print("Loading Encode File ...")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

# Initialize variables
modeType = 0
counter = 0
id = -1
imgStudent = []

while True:
    # Read frame from camera
    success, img = cap.read()
    if success:  # success is a return value from cap.read()
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    else:
        print("Error: Camera not capturing frames!")

    # Resize frame for faster processing


    # Detect faces in the frame
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    # Overlay background image
    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    # Process detected faces
    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            # Check for matching faces
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            # Find the best matching face
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                # Recognized face detected
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studentIds[matchIndex]

                # Handle first detection of a recognized face
                if counter == 0:
                    cvzone.putTextRect(imgBackground, "Loading", (275, 400))
                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

                # Handle subsequent frames with a recognized face
                if counter != 0:
                    if counter == 1:
                        # Retrieve student data from Firebase
                        studentInfo = db.reference(f'Students/{id}').get()
                        if studentInfo is not None:
                            # Download student image from storage (with error handling)
                            # Download student image from storage (with error handling)
                            try:
                                blob = bucket.get_blob(f'images/{id}.png')
                                if blob:
                                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                                    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                                else:
                                    print(f"Image download failed for student {id}.")
                            except Exception as e:
                                print(f"Error downloading student image: {e}")
                                imgStudent = []  # Set imgStudent to empty if download fails

                            # Update attendance logic (replace with your desired logic)
                        if imgStudent:  # Only process if image is downloaded successfully
                            datetimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                                                               "%Y-%m-%d %H:%M:%S")
                            secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                            if secondsElapsed > 30:
                                ref = db.reference(f'Students/{id}')
                                studentInfo['total_attendance'] += 1
                                ref.child('total_attendance').set(studentInfo['total_attendance'])
                                ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                print(f"Attendance updated for student {id}")

                            # Display student information (use imgStudent if downloaded)
                        cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                        if imgStudent:
                            imgBackground[175:175 + 216, 909:909 + 216] = imgStudent
                        else:
                            cv2.putText(imgBackground, "Image Download Failed", (808, 500),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2)

                        counter += 1

                        # Handle subsequent frames after displaying information
                    if 10 < counter < 20:
                        modeType = 2

                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    if counter <= 10:
                        # Display student details on the background image
                        cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(id), (1006, 493),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                        cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                        (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                                    cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                        if imgStudent:
                            imgBackground[175:175 + 216, 909:909 + 216] = imgStudent
                        else:
                            cv2.putText(imgBackground, "Image Download Failed", (808, 500),
                                        cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2)

                    counter += 1

                    # Reset after displaying information for a duration
                    if counter >= 20:
                        counter = 0
                        modeType = 0
                        studentInfo = []
                        imgStudent = []
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    # Handle cases where no face is detected
                else:
                    modeType = 0
                    counter = 0

                    # Display the final image
                cv2.imshow("Face Attendance", imgBackground)
                cv2.waitKey(1)



