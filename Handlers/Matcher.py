import sqlite3
from Handlers.User import User
from validators import FormValidator as FV

class Matcher:

    def __init__(self, user):
        self.current_user = user
        self.potentials = []
        self.dbconn = sqlite3.connect("./Database/dataBase.db")
        self.cursor = self.dbconn.cursor()

    def get_potentials(self):
        query = "SELECT email FROM `users` WHERE `email`!=? and `reported`=0"
        self.cursor.execute(query, (self.current_user.email,))
        res = self.cursor.fetchall()
        self.collect_results(res)
        self.filter_results()
        return self.potentials

    def collect_results(self, results):
        for item in results:
            user = User()
            user.get_user_by_email(item[0])
            user.get_profile()
            profile = {}
            profile["Name"] = user.firstname
            profile["last_name"] = user.lastname
            profile["Age"] = user.age
            profile["profilePic"] = user.profilePic
            profile["id"] = user.id
            profile["Fame"] = user.fame
            profile["gender"] = user.gender
            profile["sexuality"] = user.sexuality
            profile["interests"] = user.interests
            self.potentials.append(profile)

    def filter_results(self):
        #query = "SELECT userA FROM `blocked` WHERE `userB`=?"
        #self.cursor.execute(query, (self.current_user.id,))
        for item in reversed(self.potentials):
            if self.current_user.gender == "male" and self.current_user.sexuality == "heterosexual":
                if item["gender"] == "male" or item["sexuality"] == "homosexual":
                    self.potentials.remove(item)
            if self.current_user.gender == "male" and self.current_user.sexuality == "homosexual":
                if item["gender"] == "female" or item["sexuality"] == "heterosexual":
                    self.potentials.remove(item)
            if self.current_user.gender == "female" and self.current_user.sexuality == "heterosexual":
                if item["gender"] == "female" or item["sexuality"] == "homosexual":
                    self.potentials.remove(item)
            if self.current_user.gender == "female" and self.current_user.sexuality == "homosexual":
                if item["gender"] == "male" or item["sexuality"] == "heterosexual":
                    self.potentials.remove(item)
            if self.current_user.gender == "male" and self.current_user.sexuality == "bisexual":
                if item["gender"] == "female" and item["sexuality"] == "homosexual":
                    self.potentials.remove(item)
                if item["gender"] == "male" and item["sexuality"] == "heterosexual":
                    self.potentials.remove(item)
            if self.current_user.gender == "female" and self.current_user.sexuality == "bisexual":
                if item["gender"] == "male" and item["sexuality"] == "homosexual":
                    self.potentials.remove(item)
                if item["gender"] == "female" and item["sexuality"] == "heterosexual":
                    self.potentials.remove(item)

    def get_filtered_potentials(self, filters):
        self.get_potentials()
        if int(filters["min_interests"]) <= 0:
            filters["min_interests"] = 1
        if int(filters["max_interests"]) >= 5 or int(filters["max_interests"] == 0):
            filters["max_interests"] = 5
        if int(filters["min_age"]) < 18 or int(filters["min_age"] == 0):
            filters["min_age"] = 18
        if int(filters["max_age"]) > 99 or int(filters["max_age"] == 0):
            filters["max_age"] = 99
        if int(filters["min_fame"]) <= 0:
            filters["min_fame"] = 0
        if int(filters["max_fame"]) > 100 or int(filters["max_fame"] == 0):
            filters["max_fame"] = 100
        results = []
        for item in self.potentials:
            count = 0
            for thing in item["interests"]:
                if thing in self.current_user.interests:
                    count += 1
            if int(filters["min_fame"]) <= item["Fame"] <= int(filters["max_fame"]) and int(filters["min_age"]) <= item["Age"] <= int(filters["max_age"]) and int(filters["min_interests"]) < count < int(filters["max_interests"]):
                    results.append(item)
        return results


    @staticmethod
    def send_notification(userA, userB):
        pass

    @staticmethod
    def match_users(userA, userB):
        conn = sqlite3.connect("./Database/dataBase.db")
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM `matches` WHERE `userA`=? AND `userB`=?"
        cursor.execute(query, (userA, userB,))
        res = cursor.fetchall()
        if res[0][0] == 0:
            query = "INSERT INTO `matches` (userA, userB) VALUES (?, ?)"
            cursor.execute(query, (userA, userB,))
            conn.commit()
        query = "SELECT COUNT(*) FROM `matches` WHERE `userB`=? AND `userA`=?"
        cursor.execute(query, (userA, userB,))
        res = cursor.fetchall()
        if res[0][0] > 0:
            Matcher.send_notification(userA, userB)
