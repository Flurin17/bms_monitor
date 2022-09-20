from os import terminal_size
from bs4 import BeautifulSoup as bs
from threading import Thread
import lxml
from datetime import datetime, timedelta
from dhooks import Webhook, Embed
import requests
import time
import pymongo
from credentials import *
client = pymongo.MongoClient(mongoDbUrl)
gradesDB = client.grades.bms


def log(msg):
    logmsg = "[{0}]: {1}".format(datetime.now(), msg)
    try:
        print(logmsg)
        logmsg = logmsg + "\n"
        with open ('logging.txt', 'a', newline="") as f:
            f.write(logmsg)
    except:
        print("Can't save")

def sendWebhook(courseName, gradeTitle, value):
    hook = Webhook(webhookname)
    embed = Embed(
        description='Neue Note online',
        color=0x5CDBF0,
        timestamp='now'  # sets the timestamp to current time
        )
    embed.add_field(name='Fach', value=courseName)
    embed.add_field(name='Name', value=gradeTitle)
    embed.add_field(name='Note', value=value)
    hook.send(embed=embed)

    log("Sent webhook")



class Grade:
    def __init__(self, name, note):
        self.name = name
        self.note = note

class course:
    def __init__(self, courseShort, courseName, id):
        self.courseShort = courseShort
        self.courseName = courseName
        self.id = id
    

class monitor:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()




    def getHash(self):
        while True:
            try:
                r = self.session.get(
                url='https://intranet.tam.ch/bmz',
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                }
                )
            except:
                log("Somenthing failed")
                continue
            
            if r.status_code == 200:
                try:
                    soup = bs(r.text, 'lxml')
                    self.hash = soup.find("input", {"name":"hash"})['value']
                    log(f"Got hash {self.hash}")
                    break

                except Exception as e:
                    log(f"Failed to grab hash {e}")
    def postLogin(self):
        while True:
            try:
                r = self.session.post(
                url='https://intranet.tam.ch/bmz',
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                },
                data={
                    'hash': self.hash,
                    'loginschool': 'bmz',
                    'loginuser': self.email,
                    'loginpassword': self.password,
                    'captcha[id]': "f33d99eed4b1a81583bf15a1c4114a40",
                    'captcha[input]': "2774uusy",
                },
                allow_redirects=False
                )
            except:
                log("Somenthing failed")
                continue
            
            if r.status_code == 302:
                if r.headers['Location'] == "/bmz/":
                    log("Logged in")
                    break
            else:
                log("Somenthing failed")
                continue

    def getUserId(self):
        while True:
            try:
                r = self.session.get(
                url='https://intranet.tam.ch/bmz/gradebook',
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                }
                )
            except:
                log("Somenthing failed")
                continue
            
            if r.status_code == 200:
                try:
                    websiteText = r.text
                    self.userId = websiteText.split("intranet.ui.profile.getAllPersonalInfos('")[1].split("', ")[0]
                    log(f"Got user ID {self.userId}")
                    break

                except Exception as e:
                    log(f"Failed to grab userID {e}")

    def getPeriods(self):
        while True:
            try:
                r = self.session.get(
                url='https://intranet.tam.ch/bmz/gradebook/ajax-get-periods',
                headers={
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
                    'accept': '*/*',
                }
                )
            except:
                log("Somenthing failed")
                continue
            
            if r.status_code == 200:
                try:
                    jsonWebsite = r.json()
                    self.periodId = jsonWebsite['data'][-1]['periodId']
                    log(f"Got Period ID {self.periodId}")
                    break

                except Exception as e:
                    log(f"Failed to grab period {e}")

    def getClasses(self):
        while True:
            try:
                r = self.session.post(
                url='https://intranet.tam.ch/bmz/gradebook/ajax-get-courses-for-period',
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                },
                data={
                    'periodId': self.periodId,
                    'view': 'list'
                }

                )
            except:
                log("Somenthing failed")
                continue

            if r.status_code == 200:
                try:
                    jsonWebsite = r.json()
                    self.courses = []
                    for classS in jsonWebsite['data']:
                        log(f"{classS['courseName']} {classS['courseShort']} {classS['courseId']}")
                        self.courses.append(course(classS['courseShort'], classS['courseName'] ,classS['courseId']))
                    break

                except Exception as e:
                    log(f"Failed to Classes {e}")

    def getGrade(self, course):
        while True:
            try:
                r = self.session.post(
                url='https://intranet.tam.ch/bmz/gradebook/ajax-list-get-grades',
                headers={
                    'content-type': 'application/x-www-form-urlencoded',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
                    'accept': '*/*',
                },
                data={
                    'studentId': self.userId,
                    'courseId': course.id,
                    'periodId': self.periodId
                }

                )
            except:
                log("Somenthing failed")
                continue
            
            if r.status_code == 200:
                try:
                    jsonWebsite = r.json()
                    for grade in jsonWebsite['data']:
                        already = gradesDB.find_one({"title":grade['title'],"value":grade['value'], "courseShort": course.courseShort})
                        if already != None:
                             log(f"Grade Already Exists {course.courseName} {grade['title']} {grade['value']}")
                        else:
                            gradeInserted = gradesDB.insert_one({'courseName': course.courseName, 'courseShort': course.courseShort, 'title':grade['title'], 'value':grade['value']})
                            sendWebhook(course.courseName, grade['title'], grade['value'])
                            log(f"FOUND NEW GRADE {course.courseName} {grade['title']} {grade['value']}")
                    break

                except Exception as e:
                    log(f"Failed get Grades {e}")


    def start(self):
        self.getHash()
        self.postLogin()
        self.getUserId()
        self.getPeriods()
        self.getClasses()
        while True:
            self.getUserId()
            for course in self.courses:
                self.getGrade(course)
            time.sleep(600)
            



monitor(username, password).start()
