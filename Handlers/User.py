import sqlite3
import bcrypt
from validators import FormValidator as FV


class User:

    def __init__(self):
        self.id = None
        self.username = None
        self.email = None
        self.password = None
        self.verified = None
        self.verificationKey = None
        self.reported = None
        self.firstname = None
        self.lastname = None
        self.gender = None
        self.age = None
        self.sexuality = None
        self.fame = None
        self.profileVisits = None
        self.latitude = None
        self.longitude = None
        self.city = None
        self.bio = None
        self.profilePic = None
        self.interests = []
        self.dbconn = sqlite3.connect("./Database/dataBase.db")
        self.dbconn.row_factory = sqlite3.Row
        self.cursor = self.dbconn.cursor()

    def user_exists(self, email):
        query = "SELECT count(*) FROM `users` WHERE `email`=?"
        self.cursor.execute(query, (email,))
        result = self.cursor.fetchall()
        if result[0][0] > 0:
            return True
        else:
            return False

    def get_user_by_email(self, email):
        query = "SELECT * FROM `users` WHERE `email`=?"
        self.cursor.execute(query, (email,))
        result = self.cursor.fetchall()
        if result:
            for item in result:
                self.id = item["id"]
                self.username = item["username"]
                self.email = item["email"]
                self.password = item["password"]
                self.verified = item["verified"]
                self.verificationKey = item["verificationKey"]
                self.reported = item["reported"]
    
    def get_user_by_id(self, uid):
        query = "SELECT * FROM `users` WHERE `id`=?"
        self.cursor.execute(query, (uid,))
        result = self.cursor.fetchall()
        if result:
            for item in result:
                self.id = item["id"]
                self.username = item["username"]
                self.email = item["email"]
                self.password = item["password"]
                self.verified = item["verified"]
                self.verificationKey = item["verificationKey"]
                self.reported = item["reported"]

    def get_profile(self):
        query = "SELECT firstName, lastName, gender, age, preference, fame, profileVisits, bio, profilePic FROM `profile` WHERE `userId`=?"
        self.cursor.execute(query, (self.id,))
        result = self.cursor.fetchall()
        profile = {}
        if len(result) > 0:
            profile["Username"] = self.username
            profile["Email"] = self.email
            profile["First Name"] = result[0]["firstName"]
            profile["Last Name"] = result[0]["lastName"]
            profile["Gender"] = result[0]["gender"]
            profile["Age"] = result[0]["age"]
            profile["Sexuality"] = result[0]["preference"]
            profile["Fame"] = result[0]["fame"]
            profile["Profile Visits"] = result[0]["profileVisits"]
            profile["Bio"] = result[0]["bio"]
            if profile["Gender"] == 1:
                profile["Gender"] = "male"
            elif profile["Gender"] == 0:
                profile["Gender"] = "female"
            if profile["Sexuality"] == 0:
                profile["Sexuality"] = "homosexual"
            elif profile["Sexuality"] == 1:
                profile["Sexuality"] = "heterosexual"
            elif profile["Sexuality"] == 2:
                profile["Sexuality"] = "bisexual"
            self.firstname = profile["First Name"]
            self.lastname = profile["Last Name"]
            self.gender = profile["Gender"]
            self.age = profile["Age"]
            self.bio = profile["Bio"]
            self.fame = profile["Fame"]
            self.profileVisits = profile["Profile Visits"]
            profile["Fame"] = self.update_fame()
            self.sexuality = profile["Sexuality"]
            self.profilePic = result[0]["profilePic"]
            self.get_interests()
            return profile
        else:
            return False

    def update_fame(self):
        query = "SELECT * FROM `matches` WHERE `userB`=?"
        self.cursor.execute(query, (self.id,))
        res = self.cursor.fetchall()
        likes = len(res)
        if self.profileVisits == 0:
            return 0
        fame = likes / self.profileVisits
        fame *= 100
        query = "UPDATE `profile` SET `fame`=? WHERE `userId`=?"
        self.cursor.execute(query, (int(fame), self.id, ))
        self.dbconn.commit()
        return fame

    def get_user_by_username(self, username):
        query = "SELECT * FROM `users` WHERE `username`=?"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchall()
        for item in result:
            self.id = item["id"]
            self.username = item["username"]
            self.email = item["email"]
            self.password = item["password"]
            self.verified = item["verified"]
            self.verificationKey = item["verificationKey"]
            self.reported = item["reported"]

    def save_user(self):
        query = "INSERT INTO `users`(username, email, password, verificationKey) VALUES(?, ?, ?, ?)"
        self.cursor.execute(query, (self.username, self.email, self.password, self.verificationKey))
        self.dbconn.commit()
        query = "SELECT id FROM `users` WHERE `username`=? AND `email`=?"
        self.cursor.execute(query, (self.username, self.email,))
        res = self.cursor.fetchall()
        self.id = res[0][0]

    def password_correct(self, password):
        if bcrypt.checkpw(password, self.password):
            return True
        else:
            return False

    def verify_user(self, verificationKey):
        if not self.verified:
            if self.verificationKey == verificationKey:
                self.verified = True
                query = "UPDATE `users` SET `verified`=TRUE WHERE `id`=?"
                self.cursor.execute(query, (self.id,))
                self.dbconn.commit()
                return True
            else:
                return False

    def update_verification_key(self, new_key):
        query = "UPDATE `users` SET `verificationKey`=? WHERE `id`=?"
        self.cursor.execute(query, (new_key, self.id,))
        self.dbconn.commit()
        self.verificationKey = new_key

    def update_email(self, new_email):
        if self.user_exists(new_email):
            return False
        else:
            query = "UPDATE `users` SET `email`=? WHERE `id`=?"
            self.cursor.execute(query, (new_email, self.id))
            self.dbconn.commit()
            self.email = new_email
            return True

    def update_username(self, username):
        if self.user_exists(self.email):
            return False
        else:
            query = "UPDATE `users` SET `username`=? WHERE `id`=?"
            self.cursor.execute(query, (username, self.id))
            self.dbconn.commit()
            return True

    def update_password(self, new_password):
        if FV.PasswordValid(new_password):
            query = "UPDATE `users` SET `password`=? WHERE `id`=?"
            hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            self.cursor.execute(query, (hashed, self.id))
            self.dbconn.commit()
            return True
        else:
            return False

    def update_firstname(self, new_firstname):
        if FV.FieldOutOfRange(new_firstname, 3, 32):
            return False
        else:
            query = "UPDATE `profile` SET `firstname`=? WHERE `userId`=?"
            self.cursor.execute(query, (new_firstname, self.id))
            self.dbconn.commit()
            self.firstname = new_firstname
            return True

    def update_lastname(self, new_lastname):
        if FV.FieldOutOfRange(new_lastname, 3, 32):
            return False
        else:
            query = "UPDATE `profile` SET `lastname`=? WHERE `userId`=?"
            self.cursor.execute(query, (new_lastname, self.id))
            self.dbconn.commit()
            self.lastname = new_lastname
            return True

    def update_age(self, new_age):
        age = int(new_age)
        if age > 17:
            query = "UPDATE `profile` SET `age`=? WHERE `userId`=?"
            self.cursor.execute(query, (age, self.id))
            self.dbconn.commit()
            self.age = age
            return True
        else:
            return False

    def update_bio(self, bio):
        if len(bio) > 1:
            query = "UPDATE `profile` SET `bio`=? WHERE `userId`=?"
            self.cursor.execute(query, (bio, self.id))
            self.dbconn.commit()
            self.bio = bio
            return True
        else:
            return False
    
    def update_sexuality(self, new_preference):
        if int(new_preference) > -1 and int(new_preference) < 3:
            query = "UPDATE `profile` SET `preference`=? WHERE `userId`=?"
            self.cursor.execute(query, (new_preference, self.id))
            self.dbconn.commit()
            return True
        else:
            return False

    def update_location(self, city):
        if len(city) != 0:
            query = "UPDATE `location` SET `lat`=?, `lon`=?, `area`=? WHERE `id`=?"
            self.cursor.execute(query, (self.latitude, self.longitude, self.city, self.id))
            self.dbconn.commit()
            return True
        else:
            return False

    def update_gender(self, gender):
        print("gender ", gender)
        if gender == "0" or gender == "1":
            print("here")
            query = "UPDATE `profile` SET `gender`=? WHERE `userId`=?"
            self.cursor.execute(query, (gender, self.id))
            self.dbconn.commit()
            return True
        else:
            return False

    def add_location(self, city):
        if len(city) != 0:
            query = "INSERT INTO `location` VALUES (?, ?, ?, ?)"
            self.cursor.execute(query, (self.id, self.latitude, self.longitude, self.city))
            self.dbconn.commit()
            return True
        else:
            return False
    
    def save_profile(self, req):
        profile_fields = {"first_name", "last_name", "age", "gender", "sexuality", "bio"}
        for item in profile_fields:
            res = req.get(item, False)
            if res is False:
                return False
        self.firstname = req["first_name"]
        self.lastname = req["last_name"]
        self.age = req["age"]
        self.gender = req["gender"]
        self.sexuality = req["sexuality"]
        self.bio = req["bio"]
        query = "INSERT INTO `profile` (userId, firstName, lastName, gender, age, preference, bio) VALUES (?, ?, ?, ?, ?, ?, ?)"
        self.cursor.execute(query, (self.id, self.firstname, self.lastname, self.gender, self.age, self.sexuality, self.bio))
        self.dbconn.commit()

    def update_profile(self, req):
        if "first_name" in req:
            self.update_firstname(req["first_name"])
        if "last_name" in req:
            self.update_lastname(req["last_name"])
        if "age" in req:
            self.update_age(req["age"])
        if "gender" in req:
            self.update_gender(req["gender"])
        if "bio" in req:
            self.update_bio(req["bio"])
        if "sexuality" in req:
            self.update_sexuality(req["sexuality"])

    def save_image(self, filename):
        query = "SELECT count(*) from `images` where `userId`=?"
        self.cursor.execute(query, (self.id,))
        result = self.cursor.fetchall()
        if result[0][0] > 5:
            return False
        else:
            query = "INSERT INTO `images` (userId, imageName) VALUES (?, ?)"
            self.cursor.execute(query, (self.id, filename))
            self.dbconn.commit()
            return True
    
    def get_images(self):
        query = "SELECT imageName FROM `images` WHERE `userId`=?"
        self.cursor.execute(query, (self.id,))
        result = self.cursor.fetchall()
        images = []
        for item in result:
            images.append(item[0])
        return images

    def delete_image(self, image):
        query = "DELETE FROM `images` WHERE `imageName`=? AND `userId`=?"
        self.cursor.execute(query, (image, self.id))
        self.dbconn.commit()

    def set_profile_picture(self, image):
        self.profilePic = image
        query = "UPDATE `profile` SET profilePic=? WHERE `userId`=?"
        self.cursor.execute(query, (image, self.id,))
        self.dbconn.commit()

    def add_interest(self, interest):
        self.get_interests()
        if len(self.interests) < 7:
            query = "SELECT id FROM `interests` WHERE `interest`=?"
            self.cursor.execute(query, (interest,))
            res = self.cursor.fetchall()
            if res[0][0]:
                query = "SELECT * FROM `userInterests` WHERE `userId`=? and `interestID`=?"
                self.cursor.execute(query, (self.id, res[0][0]))
                count = self.cursor.fetchall()
                if not count:
                    query = "INSERT INTO `userInterests` (userId, interestID) VALUES (?, ?)"
                    self.cursor.execute(query, (self.id, res[0][0]))
                    self.dbconn.commit()
    
    def get_interests(self):
        query = "SELECT `interests`.`interest` FROM `interests` JOIN `userInterests` ON `interests`.`id`=`userInterests`.`interestID` WHERE `userInterests`.`userId`=?"
        self.cursor.execute(query, (self.id,))
        res = self.cursor.fetchall()
        for item in res:
            self.interests.append(item[0])

    def remove_interest(self, interest):
        if interest in self.interests:
            self.interests.remove(interest)
        query = "SELECT id FROM `interests` WHERE `interest`=?"
        self.cursor.execute(query, (interest,))
        res = self.cursor.fetchall()
        query = "DELETE FROM `userInterests` WHERE `userId`=? AND `interestID`=?"
        self.cursor.execute(query, (self.id, res[0][0]))
        self.dbconn.commit()

    def get_matches(self):
        matches = []
        query = "SELECT userB FROM `matches` WHERE `userA`=?"
        self.cursor.execute(query, (self.id,))
        res = self.cursor.fetchall()
        for item in res:
            query = "SELECT COUNT(*) FROM `matches` WHERE `userA`=? AND `userB`=?"
            self.cursor.execute(query, (item[0], self.id,))
            res = self.cursor.fetchall()
            if res[0][0] > 0:
                profile = {}
                user = User()
                user.get_user_by_id(item[0])
                user.get_profile()
                profile["id"] = user.id
                profile["profilePic"] = user.profilePic
                profile["first_name"] = user.firstname
                profile["last_name"] = user.lastname
                profile["age"] = user.age
                matches.append(profile)
        return matches

    def block(self, target):
        query = "INSERT INTO `blocked` (userA, userB) VALUES (?, ?)"
        self.cursor.execute(query, (self.id, target.id))
        self.dbconn.commit()

    def report(self, target):
        query = "UPDATE `users` SET `reported`=1 WHERE `id`=?"
        self.cursor.execute(query, (target.id,))
        self.dbconn.commit()

    def viewed_by(self, peep):
        viewer = peep.firstname + " " + peep.lastname
        param = viewer + " checked out your profile! Ooh-la-la!"
        query = "UPDATE `profile` SET `profileVisits` = `profileVisits` + 1 WHERE `userId`=?"
        self.cursor.execute(query, (self.id, ))
        query = "INSERT INTO `notifications` (userId, message, received) VALUES (?, ?, 0)"
        self.cursor.execute(query, (self.id, param, ))
        self.dbconn.commit()

    def liked_by(self, peep):
        viewer = peep.firstname + " " + peep.lastname
        param = viewer + " likes you! How embarrassing!"
        query = "INSERT INTO `notifications` (userId, message, received) VALUES (?, ?, 0)"
        self.cursor.execute(query, (self.id, param, ))
        self.dbconn.commit()

    def blocked_by(self, peep):
        viewer = peep.firstname + " " + peep.lastname
        param = viewer + " blocked you! Tsk tsk!"
        query = "INSERT INTO `notifications` (userId, message, received) VALUES (?, ?, 0)"
        self.cursor.execute(query, (self.id, param, ))
        self.dbconn.commit()

    def message_by(self, peep):
        viewer = peep.firstname + " " + peep.lastname
        param = viewer + " sent you a message! What does it say?"
        query = "INSERT INTO `notifications` (userId, message, received) VALUES (?, ?, 0)"
        self.cursor.execute(query, (self.id, param, ))
        self.dbconn.commit()

    def get_notifications(self):
        query = "SELECT message, timestamp FROM `notifications` where `received`=0 AND `userId`=?"
        self.cursor.execute(query, (self.id,))
        notifications = self.cursor.fetchall()
        return notifications

    def clear_notifications(self):
        query = "UPDATE `notifications` SET `received`=1 WHERE `userId`=?"
        self.cursor.execute(query, (self.id,))
        self.dbconn.commit()