# pip install cmake
# conda install -c conda-forge dlib
# pip install face-recognition
# pip install scikit-image


from flask import Flask, render_template, request, session, url_for, redirect, jsonify,send_from_directory
import pymysql
import time
import cv2
import datetime
import imutils
import threading
app = Flask(__name__)
app.secret_key = 'random string'
from imutils.video import VideoStream
import threading
import time
outputFrame = None
lock = threading.Lock()
import os
from flask import Flask, render_template, Response

from mark_attendance import mark_your_attendance
from register import register_yourself

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

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    if 'user' in session:
        return render_template('home.html', user=session['user'])
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user')
    session.pop('userid')
    return redirect(url_for('index'))

@app.route('/login', methods=["GET","POST"])
def login():
    msg = ''
    if request.method == "POST":
        try:
            session.pop('user',None)
            username = request.form.get("email")
            password = request.form.get("pass")
            con = dbConnection()
            cursor = con.cursor()
            cursor.execute('SELECT * FROM userdetailscctv WHERE email = %s AND password = %s', (username, password))
            result = cursor.fetchone()
            if result:
                session['user'] = result[1]
                session['userid'] = result[0]
                return redirect(url_for('home'))
            else:
                return redirect(url_for('index'))
        except Exception as error:
            print("Exception occured at login")
            print(error)
            return redirect(url_for('index'))
        finally:
            dbClose()
    #return redirect(url_for('index'))
    return redirect(url_for('index'))


@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            email = request.form.get("email")
            mobile = request.form.get("mobile")
            password = request.form.get("pass")
            con = dbConnection()
            cursor = con.cursor()
            sql = "INSERT INTO userdetailscctv (name, email, mobile, password) VALUES (%s, %s, %s, %s)"
            val = (name, email, mobile, password)
            cursor.execute(sql, val)
            con.commit()
            return redirect(url_for('index'))
        except:
            print("Exception occured at login")
            return redirect(url_for('index'))
        finally:
            dbClose()
    return redirect(url_for('index'))

########################################################################################################################
#                                           Motion Detector
########################################################################################################################

import cv2
from datetime import datetime
import random
from datetime import date

def in_out():
    cap = cv2.VideoCapture(0)
    now = datetime.now()
    today = date.today()

    right, left = "", ""

    while True:
        _, frame1 = cap.read()
        frame1 = cv2.flip(frame1, 1)
        _, frame2 = cap.read()
        frame2 = cv2.flip(frame2, 1)

        diff = cv2.absdiff(frame2, frame1)
        
        diff = cv2.blur(diff, (5,5))
        
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        _, threshd = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
        
        contr, _ = cv2.findContours(threshd, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        x = 300
        if len(contr) > 0:
            max_cnt = max(contr, key=cv2.contourArea)
            x,y,w,h = cv2.boundingRect(max_cnt)
            cv2.rectangle(frame1, (x, y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame1, "MOTION", (10,80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2)
            
        
        if right == "" and left == "":
        
            if x > 500:
                right = True
            
            elif x < 200:
                left = True
                
        elif right:
            if x < 200:
                random_val = random.randint(0,9999)
                print("to left")
                x = 300
                right, left = "", ""
                
                current_time = now.strftime("%H:%M")
                cv2.imwrite("static/visitors/in/in1_"+str(random_val)+".jpg", frame1)


                con = dbConnection()
                cursor = con.cursor()

                img_name = "static/visitors/in/in1_"+str(random_val)+".jpg"
                sql = "INSERT INTO motion_detect (imgName,imgDate, imgTime) VALUES (%s, %s, %s)"
                val = (str(img_name), str(today), str(current_time))
                cursor.execute(sql, val)
                con.commit()
            
        elif left:
            if x > 500:
                random_val = random.randint(0,9999)
                print("to right")
                x = 300
                right, left = "", ""
                current_time = now.strftime("%H:%M")
                cv2.imwrite("static/visitors/out/out1_"+str(random_val)+".jpg", frame1)

                con = dbConnection()
                cursor = con.cursor()

                img_name = "static/visitors/out/out1_"+str(random_val)+".jpg"
                sql = "INSERT INTO motion_detect (imgName,imgDate, imgTime) VALUES (%s, %s, %s)"
                val = (str(img_name), str(today), str(current_time))
                cursor.execute(sql, val)
                con.commit()
        
        cv2.imshow("", frame1)
        
        k = cv2.waitKey(1)
        
        if k == 27:
            cap.release()
            cv2.destroyAllWindows()
            break

@app.route('/detectmotion',methods=["GET","POST"])
def detectmotion():
    if request.method=="POST":

        in_out()

        return render_template('getimages.html', user=session['user'])
    return render_template('getimages.html', user=session['user'])
    
@app.route('/getimages', methods=["GET","POST"])
def getimages():
    if 'user' in session:
        if request.method == "POST":
            date = request.form.get("date")
            time1 = request.form.get("time")
            con = dbConnection()
            cursor = con.cursor()
            
            if date == '' or time1 == '':
                
                sql = "SELECT * FROM motion_detect"
                cursor.execute(sql)
            else:
                print("SELECT * FROM motion_detect where date='"+str(date)+"'")                
                sql = "SELECT * FROM motion_detect where imgDate=%s and imgTime=%s"
                val = (date,time1)
                cursor.execute(sql,val)

            result = cursor.fetchall()
            
            return render_template('displayimage.html',result=result, user=session['user'])
        return render_template('getimages.html', user=session['user'])
    return redirect(url_for('index'))

########################################################################################################################
#                                           start camera
########################################################################################################################
@app.route('/registerperson', methods=["GET","POST"])
def registerperson():
    if request.method == "POST":
        username = request.form.get("username")
        jobprofile = request.form.get("jobprofile")
        joindate = request.form.get("joindate")
        
        print(username, jobprofile, joindate)

        register_yourself(username, jobprofile, joindate)

        return render_template('registerperson.html')
    return render_template('registerperson.html')

@app.route('/livefeed')
def livefeed():
    """Video streaming home page."""
    global usernamelist
    global vs
    global total
    total=0
   
    # vs = VideoStream(src=0).start()
    marked,studentname,dt = mark_your_attendance()

    return render_template('registerperson.html')  

@app.route('/getvideos', methods=["GET","POST"])
def getvideos():
    if 'user' in session:
        if request.method == "POST":
            date = request.form.get("date")
            time = request.form.get("time")
            con = dbConnection()
            cursor = con.cursor()
            cursor.execute("SELECT * FROM videodetails where date='"+date+"'")
            result = cursor.fetchall()
            
            return render_template('displayvideo.html',result=result, user=session['user'])
        return render_template('getvideos.html', user=session['user'])
    return redirect(url_for('index'))

@app.route("/get_file",methods=["GET","POST"])
def get_file():
    path=''
    if request.method == "GET":
        filename = request.args["filename"]
        path=filename
    
        return send_from_directory('', path, as_attachment=True)
    return send_from_directory('', path, as_attachment=True)


if __name__ == '__main__':
    # app.run(debug=True)
    app.run('0.0.0.0')