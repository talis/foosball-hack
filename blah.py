#!/usr/bin/env python2.7
from multiprocessing import Process, Value
import RPi.GPIO as GPIO
import os
import time
import pyttsx
import hipchat
import time
import os, os.path
import ConfigParser
import urllib2
import subprocess
import datetime
import fileinput
import tweepy

name = 'John Motson'
hipchatApiKey = os.environ.get('HIPCHAT_API_KEY')
hipster = hipchat.HipChat(token=hipchatApiKey)
twitter_consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_secret= os.environ.get('TWITTER_ACCESS_SECRET')

auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
auth.set_access_token(twitter_access_token, twitter_access_secret)
twitter = tweepy.API(auth)

voice = pyttsx.init()
voice.setProperty("rate", 200)
voice.say("Ready? Steady? Go!")
voice.runAndWait()

GPIO.setmode(GPIO.BCM)

def communicate(msg, say=True, hipchat=False, tweet=False):
    try:
        print msg

        if say:
            voice.say(msg)
            voice.runAndWait()
        if hipchat:
	    hipster.message_room('429941', name, msg)
        if tweet:
            twitter.update_status(msg + " #foosball")
    except Exception as e:
        print e

def call_score(team1_score, team2_score):
    drawn_p1_score = 0
    drawn_p2_score = 0

    while True:
        if drawn_p1_score == team1_score.value and drawn_p2_score == team2_score.value:
            time.sleep(0.2)
            continue

        if team1_score.value == 0 and team2_score.value == 0:
            communicate("scores have been reset")
        elif team1_score.value >= 10 or team2_score.value >= 10:
            if team2_score.value > team1_score.value:
                values = ("Blue", team2_score.value, team1_score.value)
            else:
                values = ("Pink", team1_score.value, team2_score.value)

            msg = "%s team are the winners! %d %d" % values
            communicate(msg, hipchat=True, tweet=True)

            team1_score.value = 0
            team2_score.value = 0
        else:
            if team1_score.value > team2_score.value:
                values = (team1_score.value, team2_score.value, "Pink")
            else:
                values = (team2_score.value, team1_score.value, "Blue")

            msg = "GOAL! %d %d to the %s team" % values
            communicate(msg, hipchat=True)

        drawn_p1_score = team1_score.value
        drawn_p2_score = team2_score.value

def ir_sensor(pin, score):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    last_goal_time = time.time()

    while True:
        print "waiting"
        GPIO.wait_for_edge(pin, GPIO.FALLING)
        print "waited"
        if time.time() - last_goal_time > 2:
            last_goal_time = time.time()
            if score.value < 10:
                score.value += 1

def reset_switch(pin, player1_score, player2_score):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    last_reset = time.time()

    while True:
        GPIO.wait_for_edge(pin, GPIO.RISING)
        if time.time() - last_reset > 2:
            player1_score.value = 0
            player2_score.value = 0

            last_reset = time.time()

def internet_on():
    try:
        urllib2.urlopen('https://api.hipchat.com', timeout=1)
        return True
    except urllib2.URLError as err:
        return False

def get_ip():
    cmd = "ifconfig eth0 | awk '/inet addr/ { print $2 } '"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.wait()
    return process.stdout.read().split(':')[1]

def wait_for_access():
    while (internet_on() == False):
        time.sleep(2)

    communicate("foosball table up and running on %s" % get_ip(), say=False, hipchat=True)

def main():
    wait_for_access()

    player1_score = Value('i', 0)
    player2_score = Value('i', 0)

    p2 = Process(target=ir_sensor, args=(10, player1_score))
    p3 = Process(target=ir_sensor, args=(11, player2_score))
    p4 = Process(target=reset_switch, args=(27, player1_score, player2_score))

    p2.start()
    p3.start()
    p4.start()

    call_score(player1_score, player2_score)

if __name__ == '__main__':
    main()
