#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#vi: set ai sta et ts=8 sts=4 sw=4 tw=79 wm=0 cc=+1 lbr fo=croq :
# Copyright (C) Nyimbi Odero,2023

"""A one line summary of the crontab
This implementation loads the crontab file into memory and then runs an infinite loop, checking every minute if any scheduled task needs to be run. If a task matches the current time, it runs it in a subprocess and waits for it to finish before moving on.

By using a simple sleep-based approach, this implementation uses minimal compute resources as it only wakes up once per minute to check if any tasks need to be run. This is a very lightweight approach that should work well for most use cases.

"""

import time
import subprocess

def run_command(command):
    # Run the command in a subprocess and wait for it to finish
    process = subprocess.Popen(command, shell=True)
    process.wait()
    return process.returncode

def parse_crontab_line(line):
    # Parse a single crontab line to get the schedule and command
    schedule_str, command = line.strip().split('\t')
    schedule = schedule_str.split()
    return schedule, command

def should_run(schedule):
    # Check if the current time matches the schedule
    now = time.localtime()
    if int(schedule[0]) != now.tm_min and schedule[0] != '*':
        return False
    if int(schedule[1]) != now.tm_hour and schedule[1] != '*':
        return False
    if int(schedule[2]) != now.tm_mday and schedule[2] != '*':
        return False
    if int(schedule[3]) != now.tm_mon and schedule[3] != '*':
        return False
    if int(schedule[4]) != now.tm_wday and schedule[4] != '*':
        return False
    return True

# Load the crontab file
with open('/etc/crontab') as f:
    crontab = f.readlines()

while True:
    # Loop through the crontab lines and run any that match the current time
    for line in crontab:
        schedule, command = parse_crontab_line(line)
        if should_run(schedule):
            run_command(command)
    # Sleep for one minute before checking again
    time.sleep(60)



