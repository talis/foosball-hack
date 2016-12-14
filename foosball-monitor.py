#!/usr/bin/env python2.7
from multiprocessing import Process, Value
import RPi.GPIO as GPIO
import os
import time
import hipchat
import time
import os, os.path
import ConfigParser
import urllib2
import subprocess
import datetime
import fileinput
import tweepy
import signal
import requests
from subprocess import call

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

GPIO.setmode(GPIO.BCM)

class State(object):
    def __init__(self):
        self.start_time = -1
        self.end_time = -1
        self.conclusion_reason = 'na'
        self.team_one_id = '0'
        self.team_two_id = '1'
        self.team_one_score = 0
        self.team_two_score = 0
        self.history = []
        self.last_goal_time = time.time()

    def toJson(self):
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'conclusion_reason': self.conclusion_reason,
            'goals': self.history
        }

def internet_on():
    try:
        urllib2.urlopen('https://api.hipchat.com', timeout=1)
    except urllib2.URLError as err:
        return False
    return True

def get_ip():
    cmd = "ifconfig eth0 | awk '/inet addr/ { print $2 } '"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.wait()

    return process.stdout.read().split(':')[1]

def wait_for_access():
    while internet_on() == False:
        time.sleep(2)

    communicate("foosball table up and running on %s" % get_ip(), say=True, hipchat=True)

def send_state(state):
    requests.post('http://127.0.0.1:5000/stat', json=state.toJson())

def communicate(msg, say=True, hipchat=False, tweet=False):
    try:
        print msg

        if say:
            call(["espeak", "-v", "en", "-s160", "-p99", msg])
        if hipchat:
	    hipster.message_room('429941', name, msg)
        if tweet:
            twitter.update_status(msg + " #foosball")
    except Exception as e:
        print e

def call_score(state):
    team_one_score = state.team_one_score
    team_two_score = state.team_two_score

    if team_one_score >= 10 or team_two_score >= 10:
        if team_two_score > team_one_score:
            values = ("Blue", team_two_score, team_one_score)
        else:
            values = ("Pink", team_one_score, team_two_score)

        msg = "%s team are the winners! %d %d" % values
        communicate(msg, hipchat=True)
    elif team_one_score == team_two_score:
        msg = "%d to all" % (team_one_score)
        communicate(msg, hipchat=True)
    else:
        if team_one_score > team_two_score:
            values = (team_one_score, team_two_score, "Pink")
        else:
            values = (team_two_score, team_one_score, "Blue")

        msg = "GOAL! %d %d to the %s team" % values
        communicate(msg, hipchat=True)

def score(state, pin):
    now = time.time()
    if now - state.last_goal_time <= 2:
        # debounce the pin by two seconds
        return

    time.sleep(0.01)
    if GPIO.input(pin) != GPIO.HIGH:
        print 'phantom spike on score pin %s' % pin
        return

    state.last_goal_time = now
    if pin == 10:
        state.team_one_score += 1
        state.history.append({
            'time': now,
            'team': state.team_one_id
        })
    else:
        state.team_two_score += 1
        state.history.append({
            'time': now,
            'team': state.team_two_id
        })

    if state.start_time == -1:
        # record the start time
        # from the first goal
        state.start_time = now

    call_score(state)

    if state.team_one_score == 10 or state.team_two_score == 10:
        state.conclusion_reason = 'complete'
        state.end_time = now
        send_state(state)
        state = State()

def reset_scores(state, pin):
    time.sleep(0.01)

    if GPIO.input(pin) != GPIO.HIGH:
        print 'phantom spike on reset pin %s' % pin
        return

    communicate('scores have been reset')
    state.conclusion_reason = 'reset'
    state.end_time = time.time()
    send_state(state)

    state = State()

def supply_state(func, *args, **keywords):
    def newfunc(*fargs, **fkeywords):
        newkeywords = keywords.copy()
        newkeywords.update(fkeywords)
        return func(*(args + fargs), **newkeywords)

    newfunc.func = func
    newfunc.args = args
    newfunc.keywords = keywords
    return newfunc

def setup_pin(num, state, func):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(num, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(num, GPIO.FALLING, callback=supply_state(func, state))

def main():
    wait_for_access()

    state = State()
    setup_pin(27, state, reset_scores)
    setup_pin(10, state, score)
    setup_pin(11, state, score)
    signal.pause()

if __name__ == '__main__':
    main()
