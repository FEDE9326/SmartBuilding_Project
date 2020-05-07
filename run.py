#!/bin/bash

rm actuator.csv 
rm sensor.csv
rm environment.csv

python Policy.py &
python Actuators.py &
python Sensors.py &
python Environment.py
