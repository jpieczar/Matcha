from faker import Faker
from faker.providers import BaseProvider
from Handlers.User import User
from werkzeug.utils import secure_filename
from uuid import uuid4
import random
import bcrypt
import os
import shutil
import datetime

fake = Faker()
random.seed()
Faker.seed()

stock_photos_female = "stock_photos/Female/"
stock_photos_male = "stock_photos/Male/"
upload_path = "static/uploads/"

target_female = 100
target_male = 100

f = open("Database/interests.txt", "r")
interests = []
for i in f:
    interests.append(i[:-1])

f.close()

class Matcha(BaseProvider):

    def interest(self):
        return random.choice(interests)

    def sexuality(self):
        sexuality = [0, 1, 2]
        return random.choice(sexuality)
    
    def fame(self):
        return random.randrange(0, 10)

    def gender(self):
        gender = ["male", "female"]
        return random.choice(gender)

    def male_image(self):
        ret = "M" + str(random.randrange(1, 45)) + ".jpg"
        return ret

    def female_image(self):
        ret = "F" + str(random.randrange(1, 56)) + ".jpg"
        return ret

fake.add_provider(Matcha)
emails = []
#default dummy
if target_female > 0 or target_male > 0:
    user = User()
    user.username = "ppreez"
    user.email = "test@email.com"
    user.password = bcrypt.hashpw("P@ssword1".encode("UTF-8"), bcrypt.gensalt())
    user.verificationKey = str(uuid4().time_low)
    user.save_user()
    user.verify_user(user.verificationKey)
    profile = {}
    profile["first_name"] = "Pieter"
    profile["last_name"] = "du Preez"
    profile["gender"] = 1
    profile["sexuality"] = 1
    profile["age"] = 31
    profile["bio"] = "I am really really really really cool"
    profile["fame"] = 10000
    user.save_profile(profile)
    user.add_interest("drugs")
    user.add_interest("partying")
    user.add_interest("sleeping")

#women
for i in range(target_female):
    print("Adding user: ", i)
    pic = 0
    email = fake.email()
    if email in emails:
        continue
    else:
        emails.append(email)
    user = User()
    user.email = email
    user.username = fake.user_name()
    user.password = bcrypt.hashpw("P@ssword1".encode("UTF-8"), bcrypt.gensalt())
    user.verificationKey = str(uuid4().time_low)
    user.save_user()
    user.verify_user(user.verificationKey)
    profile = {}
    profile["first_name"] = fake.first_name_female()
    profile["last_name"] = fake.last_name()
    profile["gender"] = 0
    profile["sexuality"] = fake.sexuality()
    profile["age"] = random.randrange(18, 50)
    profile["bio"] = fake.text()[:500]
    profile["fame"] = fake.fame()
    while len(user.interests) < 5:
        user.add_interest(fake.interest())
    user.save_profile(profile)
    if not os.path.exists(upload_path + str(user.id)):
        os.mkdir(upload_path + str(user.id))
    filename = str(pic) + secure_filename(str(datetime.datetime.now(tz=None))) + ".jpg"
    pic += 1
    image_src = stock_photos_female + fake.female_image()
    image_dest = upload_path + str(user.id) + "/" + filename
    user.save_image(image_dest)
    user.set_profile_picture(image_dest)
    shutil.copy(image_src, image_dest)
    for i in range(random.randrange(0, 4)):
        filename = str(pic) + secure_filename(str(datetime.datetime.now(tz=None))) + ".jpg"
        image_src = stock_photos_female + fake.female_image()
        image_dest = upload_path + str(user.id) + "/" + filename
        pic += 1
        user.save_image(image_dest)
        shutil.copy(image_src, image_dest)

#men

for i in range(target_male):
    print ("Adding user: ", (i + target_female))
    email = fake.email()
    if email in emails:
        continue
    else:
        emails.append(email)
    user = User()
    user.email = email
    user.username = fake.user_name()
    user.password = bcrypt.hashpw("P@ssword1".encode("UTF-8"), bcrypt.gensalt())
    user.verificationKey = str(uuid4().time_low)
    user.save_user()
    user.verify_user(user.verificationKey)
    profile = {}
    profile["first_name"] = fake.first_name_male()
    profile["last_name"] = fake.last_name()
    profile["gender"] = 1
    profile["sexuality"] = fake.sexuality()
    profile["age"] = random.randrange(18, 50)
    profile["bio"] = fake.text()[:500]
    profile["fame"] = fake.fame()
    user.save_profile(profile)
    for i in range(5):
        user.add_interest(fake.interest())
    if not os.path.exists(upload_path + str(user.id)):
        os.mkdir(upload_path + str(user.id))
    filename = str(pic) + secure_filename(str(datetime.datetime.now(tz=None))) + ".jpg"
    pic += 1
    image_src = stock_photos_male + fake.male_image()
    image_dest = upload_path + str(user.id) + "/" + filename
    user.save_image(image_dest)
    user.set_profile_picture(image_dest)
    shutil.copy(image_src, image_dest)
    for i in range(random.randrange(0, 4)):
        filename = str(pic) + secure_filename(str(datetime.datetime.now(tz=None))) + ".jpg"
        image_src = stock_photos_male + fake.male_image()
        image_dest = upload_path + str(user.id) + "/" + filename
        pic += 1
        user.save_image(image_dest)
        shutil.copy(image_src, image_dest)