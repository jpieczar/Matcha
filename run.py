import os
import pickle
import json
import random
import string
import datetime
import sqlite3
import bcrypt   # Used for hashing the password.
import requests # To call other APIs, specifically for geolocation
from uuid import uuid4  # Used for email verification.
from flask import Flask, flash, json, Response, request, session, render_template, redirect, url_for
from flask_cors import CORS, cross_origin
from validators import FormValidator as FV
from Handlers import User, Matcher
from mail import sendVerificationMail, sendPasswordMail
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, send, emit

title = "Matcha"
upload_folder = "static/uploads/"
legal_extensions = {"png", "jpg", "jpeg"}
interest_list = open("Database/interests.txt")
interests = []
for i in interest_list:
    interests.append(i[:-1])
geoAPI = "http://ip-api.com/json/"

app = Flask(__name__)
cors = CORS(app, supports_credentials=True)
app.secret_key = "SECRET"
app.debug = True
app.config["upload_folder"] = upload_folder
socketio = SocketIO(app)

def get_user(session):
    if "email" in session:
        email = session["email"]
    else:
        email = ""
    user = User()
    user.get_user_by_email(email)
    return user

def get_interests():
    conn = sqlite3.connect("Database/dataBase.db")
    query = "SELECT interest FROM `interests`"
    c = conn.cursor()
    c.execute(query,)
    res = c.fetchall()
    return res

@app.route("/", methods=["GET", "POST"])
def root():
    user = get_user(session)
    if user.email:
        user.get_profile()
        matcher = Matcher(user)
        potentials = matcher.get_potentials()
        return render_template("user_card.html", title=title, session=user.email, potentials=potentials)
    else:
        return render_template("register.html", title=title, session=user.email)

@app.route("/sort/<sort_on>", methods=["GET"])
def sort(sort_on):
   user = get_user(session)
   if user.email:
       user.get_profile()
       matcher = Matcher(user)
       potentials = matcher.get_potentials()
       return render_template("user_card.html", title=title, session=user.email, potentials=potentials)

@app.route("/filter", methods=["POST"])
def filter():
    user = get_user(session)
    if user.email:
        user.get_profile()
        filters = {}
        filters["min_age"] = request.form.get("min_age")
        filters["max_age"] = request.form.get("max_age")
        filters["min_fame"] = request.form.get("min_fame")
        filters["max_fame"] = request.form.get("max_fame")
        filters["min_interests"] = request.form.get("min_interests")
        filters["max_interests"] = request.form.get("max_interests")
        for item in filters:
            if len(filters[item]) == 0:
                filters[item] = 0
        matcher = Matcher(user)
        potentials = matcher.get_filtered_potentials(filters)
        return render_template("user_card.html", title=title, session=user.email, potentials=potentials)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return redirect("/")
    elif request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        if username is None or FV.FieldOutOfRange(username, 3, 32):
            flash("Username out of range")
        if email is None or FV.FieldOutOfRange(email, 3, 32):
            flash("Email required")
        if FV.EmailInvalid(email):
            flash("Invalid email")
        if password is None:
            flash("Password is required")
        elif not FV.PasswordValid(password):
            flash("Invalid password")
        elif password != confirm:
            flash("Passwords do not match")
        user = User()        
        if len(email) > 0 and user.user_exists(email):
            flash("email taken")
        if "_flashes" in session:
            return redirect("/register")
        else:
            user = User()
            user.email = email
            user.username = username
            user.password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            """
            The variable 'password' needs to be encoded in "utf-8" in order for hashing with bcrypt to work in Python 3.
            With Python 3, strings are, by default, unicode strings.
            else: TypeError: Unicode-objects must be encoded before hashing.
            """
            user.verified = 0
            user.verificationKey = str(uuid4().time_low) # Converts uuid to int, then to string, so it's stored correctly in the database
            user.save_user()
            sendVerificationMail(user.email, user.verificationKey)
            return redirect("/verif-sent")

@app.route("/verify", methods=["GET"])
def verify():
    email = request.args.get("email")
    verif = request.args.get("uuid")
    user = User()
    user.get_user_by_email(email)
    user.verify_user(verif)
    return render_template("verified.html", title=title, session="")

@app.route("/verify-resend", methods=["GET"])
def verify_resend():
    user = get_user(session)
    if "email" in session:
        session.pop("email", None)
    print(user.email)
    return render_template("verify-resend.html", title=title, session="", email=user.email)

@app.route("/resend-verification/<string:email>", methods=["GET"])
def resend(email):
    user = User()
    user.get_user_by_email(email)
    user.update_verification_key(str(uuid4().time_low))
    sendVerificationMail(user.email, user.verificationKey)
    return redirect("/verif-sent")

@app.route("/verif-sent", methods=["GET"])
def verif_sent():
    return render_template("verif-sent.html", title=title, session="")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        if "email" in session:
            name = session["email"]
        else:
            name = ""
        return render_template("login.html", title=title, session=name)
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User()
        response = {}
        user.get_user_by_email(email)
        if user.password and user.password_correct(password.encode("utf-8")):
            response = app.make_response(({"errors": ""}, 200))
            response.set_cookie("user", email, secure=True)
            session["email"] = email
            if user.verified == 0:
                return redirect("/verify-resend")
            elif user.get_profile() is False:
                return redirect("/create-profile")
            # #set cookie here
            else:
                return redirect("/")
        else:
            flash("Invalid email or password")
            return redirect("/login")

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "GET":
        if "email" in session:
            email = session["email"]
        else:
            email = ""
        return render_template("account.html", title=title, session=email)
    elif request.method == "POST":
        if "email" in session:
            email = session["email"]
        else:
            email = ""
        user = User()
        user.get_user_by_email(email)
        req = request.form.to_dict()
        for item in list(req.keys()):
            req[item] = req[item].strip()
            if req[item] == "":
                del req[item]
        if "email" in req:
            if user.update_email(req["email"]) is False:
                flash("Email already taken")
            else:
                session["email"] = user.email
        if "username" in req:
            user2 = User()
            user2.get_user_by_username(user.username)
            if user2.update_username(req["username"]) is False:
                flash("Username already in use")
            else:
                print("eeee")
        return redirect("/account")

@app.route("/profile", methods=["GET"])
def profile():
    if request.method == "GET":
        if "email" in session:
            email = session["email"]
        else:
            email = ""
        user = User()
        user.get_user_by_email(email)
        profile = user.get_profile()
        return render_template("profile.html", title=title, session=email, profile=profile)

@app.route("/update-profile", methods=["GET", "POST"])
def update_profile():
    if "email" in session:
            email = session["email"]
    else:
        email = ""
    user = User()
    user.get_user_by_email(email)
    user.get_profile()
    if request.method == "GET":
        if "email" in session:
            email = session["email"]
        else:
            email = ""
        res = get_interests()
        interests = []
        for i in res:
            interests.append(i[0])
        return render_template("update_profile.html", title=title, session=email, profile="", age=user.age, gender=0, interests=interests, userInterests=user.interests)
    if request.method == "POST":
        req = request.form.to_dict()
        for item in list(req.keys()):
            req[item] = req[item].strip()
            if req[item] == "":
                del req[item]
        user.update_profile(req)
        return redirect("/profile")


@app.route("/create-profile", methods=["GET", "POST"])
def create_profile():
    if request.method == "GET":
        if "email" in session:
            email = session["email"]
        else:
            email = ""
        return render_template("create_profile.html", title=title, session=email)
    if request.method == "POST":
        if "email" in session:
            email = session["email"]
        else:
            email = ""
        req = request.form.to_dict()
        for item in list(req.keys()):
            req[item] = req[item].strip()
            if req[item] == "":
                return "Missing fields"
        user = User()
        user.get_user_by_email(email)
        user.save_profile(req)
        return redirect("/")

@app.route("/view-profile/<int:uid>", methods=["GET"])
def view_profile(uid):
    user = get_user(session)
    user.get_profile()
    target = User()
    target.get_user_by_id(uid)
    target.get_profile()
    images = target.get_images()
    target.viewed_by(user)
    return render_template("/view_profile.html", title=title, session=user.email, user=target, images=images)
    
@app.route("/match/<int:uid>", methods=["POST"])
def match(uid):
    user = get_user(session)
    user.get_profile()
    target = User()
    target.get_user_by_id(uid)
    Matcher.match_users(user.id, uid)
    target.liked_by(user)
    return redirect("/")

@app.route("/matches", methods=["GET"])
def matches():
    user = get_user(session)
    matches = user.get_matches()
    return render_template("/matches.html", title=title, session=user.email, matches=matches)

@app.route("/message/<int:uid>", methods=["GET", "POST"])
def message(uid):
    user = get_user(session)
    target = User()
    target.get_user_by_id(uid)
    target.get_profile()
    user.get_profile()
    conn = sqlite3.connect("./Database/dataBase.db")
    cursor = conn.cursor()
    if request.method == "GET":
        
        return render_template("message.html", title=title, session=user.email, user=target)
    if request.method == "POST":
        target.message_by(user)
        message = request.form.get("message")
        query = "INSERT INTO `messages` (senderId, receivedId, content) VALUES (?, ?, ?)"
        cursor.execute(query, (user.id, target.id, message))
        conn.commit()
        return redirect("/message/" + str(target.id))

@app.route("/block/<int:uid>", methods=["POST"])
def block(uid):
    user = get_user(session)
    user.get_profile()
    target = User()
    target.get_user_by_id(uid)
    user.block(target)
    target.blocked_by(user)
    return redirect("/")

@app.route("/report/<int:uid>", methods=["POST"])
def report(uid):
    user = get_user(session)
    target = User()
    target.get_user_by_id(uid)
    user.report(target)
    return redirect("/")


@app.route("/update-password", methods=["GET", "POST"])
def update_password():
    if "email" in session:
        email = session["email"]
    else:
        email = ""
    user = User()
    user.get_user_by_email(email)
    if request.method == "POST":
        req = request.form.to_dict()
        if user.password_correct(req["current_password"].encode("utf-8")):
            if FV.PasswordValid(req["new_password"]):
                if req["new_password"] == req["confirm_password"]:
                    user.update_password(req["new_password"])
                    flash("Password updated")
                else:
                    flash("New passwords do not match")
            else:
                flash("New password must be valid")
        else:
            flash("Password incorrect")
        return render_template("account.html", title=title, session=email)
        

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot():
    if request.method == "GET":
        return render_template("forgot_password.html", title=title)
    if request.method == "POST":
        email = request.form.get("email")
        user = User()
        user.get_user_by_email(email)
        if user.id:
            password = ''
            while not FV.PasswordValid(password):
                password = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation) for i in range(8))
            user.update_password(password)
            sendPasswordMail(user.email, password)
        return "Sent a mail"

@app.route("/logout")
def logout():
    if "email" in session:
        session.pop("email", None)
    return redirect("/")

@app.route("/gallery", methods=["GET"])
def gallery():
    user = get_user(session)
    user.get_profile()
    images = user.get_images()
    return render_template("gallery.html", title=title, session=user.email, images=images, pp=user.profilePic)

@app.route("/locate", methods=["GET"])
def locate():
    ip_addr = request.remote_addr
    email = request.args.get("email")
    user = User()
    user.get_user_by_email(email)
    r = requests.get(geoAPI)
    r = json.loads(r.text)
    user.latitude = r["lat"]
    user.longitude = r["lon"]
    user.city = r["city"]
    return ip_addr, 200


@app.route("/upload", methods=["POST"])
def upload():
    user = get_user(session)
    if request.method == "POST":
        if "image" not in request.files:
            return redirect("/gallery")
        image = request.files["image"]
        if len(image.filename) == 0:
            return redirect("/gallery")

        extension = image.filename.rsplit(".", 1)[1].lower()
        if extension not in legal_extensions:
            return redirect("/gallery")
        if image.filename == "":
            return redirect("/gallery")
        filename = secure_filename(str(datetime.datetime.now(tz=None)) + "." + extension)
        if not os.path.exists(app.config["upload_folder"] + str(user.id)):
            os.mkdir(app.config["upload_folder"] + str(user.id))
        save_path = os.path.join(app.config["upload_folder"] + str(user.id), filename)
        if user.save_image(save_path):
            image.save(save_path)
        #message = "Uploaded " + filename
        #flash(message)
        return redirect("/gallery")

@app.route("/set-profile/<path:image>")
def set_profile_picture(image):
    if "email" in session:
        email = session["email"]
    else:
        email = ""
    user = User()
    user.get_user_by_email(email)
    user.set_profile_picture(image)
    return redirect("/gallery")

@app.route("/delete-image/<path:image>")
def delete_image(image):
    if "email" in session:
        email = session["email"]
    else:
        email = ""
    user = User()
    user.get_user_by_email(email)
    user.delete_image(image)
    os.remove(image)
    return redirect("/gallery")

@app.route("/add-interest", methods=["POST"])
def add_interest():
    if request.method == "POST":
        req = request.form.to_dict()
        interest = req["interest"]
        query = "SELECT COUNT(*) FROM `interests` WHERE `interest`=?"
        conn = sqlite3.connect("./Database/dataBase.db")
        cursor = conn.cursor()
        cursor.execute(query, (interest,))
        result = cursor.fetchall()
        if result[0][0] == 0:
            query = "INSERT INTO `interests` (interest) VALUES (?)"
            cursor.execute(query, (interest,))
            conn.commit()
    return redirect("/update-profile")

@app.route("/select-interest/<path:interest>", methods=["POST"])
def select_interest(interest):
    if request.method == "POST":
        user = get_user(session)
        user.add_interest(interest)
        return redirect("/update-profile")

@app.route("/remove-interest/<path:interest>", methods=["POST"])
def remove_interest(interest):
    user = get_user(session)
    user.remove_interest(interest)
    return redirect("/update-profile")

@app.route("/notifications", methods=["GET"])
def notifications():
    user = get_user(session)
    notifications = user.get_notifications()
    user.clear_notifications()
    notif = []
    for item in notifications:
        notif.append(item["timestamp"] + ": " + item["message"])
    return render_template("notifications.html", title=title, session=user.email, notif=notif)

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", title=title)

@socketio.on('get-notifications')
def getnotifications(msg):
    user = get_user(session)
    notifications = user.get_notifications()
    emit("notifications", str(len(notifications)))

@socketio.on("get-messages")
def getmessages(msg):
    me = User()
    me.get_user_by_email(msg["data"]["me"])
    me.get_profile()
    them = User()
    them.get_user_by_id(msg["data"]["them"])
    them.get_profile()
    query = "SELECT id, content FROM `messages` WHERE `senderId`=? AND `receivedId`=?"
    conn = sqlite3.connect("./Database/dataBase.db")
    cursor = conn.cursor()
    cursor.execute(query, (me.id, them.id,))
    my_messages = cursor.fetchall()
    cursor.execute(query, (them.id, me.id,))
    their_messages = cursor.fetchall()
    response = []
    for item in my_messages:
        thing = {}
        thing["id"] = item[0]
        thing["content"] = me.firstname + " " + me.lastname + ": "+ item[1]
        response.append(thing)
    for item in their_messages:
        thing = {}
        thing["id"] = item[0]
        thing["content"] = them.firstname + " " + them.lastname + ": " + item[1]
        response.append(thing)
    response = sorted(response, key = lambda i: i['id'])
    resp = {}
    resp["data"] = response
    socketio.emit("messages", resp)

if __name__ == '__main__':
    socketio.run(app)
