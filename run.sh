#!/usr/bin/env bash
# run conf in anl server
# bash run.sh
python3 manage.py runserver localhost:8374 &>django.log &