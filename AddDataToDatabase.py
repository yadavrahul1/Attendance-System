import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-5afa0-default-rtdb.firebaseio.com/"
 })
ref = db.reference('Students')

data = {
    "1234":
        {
            "name": "Anishka Gupta",
            "major": "Mechanical",
            "starting_year": 2021,
            "total_attendance": 5,
            "standing": "6",
            "year": 4,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "1453":
        {
            "name": "Kanishka ",
            "major": "Mechanical",
            "starting_year": 2021,
            "total_attendance": 10,
            "standing": "6",
            "year": 4,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "4532":
        {
            "name": "Elon Musk",
            "major": "Physics",
            "starting_year": 2014,
            "total_attendance": 5,
            "standing": "6",
            "year": 4,
            "last_attendance_time": "2022-12-11 00:54:34"
        }
}
for key, value in data.items():
    ref.child(key).set(value)