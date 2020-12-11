#!/bin/sh

BASEPATH=$(dirname "$0")

cd $BASEPATH

python3 pipeline.py

scp my_action.py root@gtmoodle:chatbot/actions/my_actions.py