#!/bin/sh

BASEPATH=/Users/cyliu/git/rasa/qa_pipeline

cd $BASEPATH

python pipeline.py

scp my_action.py root@gtmoodle:chatbot/actions/my_action.py