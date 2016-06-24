# foosball-hack
Foosball table hack day project
===============================

Hack day project for monitoring the foosball table by using infra-red break
sensors on each goal post. Uses a speaker to announce the scores as they
happen and auto-posts to HipChat in real time as well as Tweeting the final
score when a game is complete.

Notes on setting up
===================

Ensure the following environment variables are set with correct values to be
able to post to Twitter and HipChat:

```
export TWITTER_CONSUMER_KEY="<value>"
export TWITTER_CONSUMER_SECRET="<value>"
export TWITTER_ACCESS_TOKEN="<value>"
export TWITTER_ACCESS_SECRET="<value>"
export HIPCHAT_API_KEY="<value>"

# Not currently used, but may be included later: post to Echo event logging service
export ECHO_USER="<value>"
export ECHO_PASS="<value>"
```
