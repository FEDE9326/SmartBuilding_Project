The simulator is written in Python and it is composed by 4 MQTT Client and 1 MQTT
broker. These client exchange messages through publish/subscribe mechanism. 

The environment publishes data about the solar radiation, azimuth and elevation each
second. The external light sensor collects this data and sums it up to the artificial one. In
the sensors module there is also the occupancy sensor that retrieve to us a random
number of people (from 0 to 7). All these data are collected and published. The policy
module gets the data and verify if the internal light is greater than the required one. If the
internal light is lower there are two possibilities:
1. Firstly, try to move up the shadowing system by 1 step. This is a forecast since we know
how much external light there is outside thanks to the external light sensor and what is
the gain in light moving up by 1 step. The shadowing system cannot be moved up by 2
or more steps because of our control strategy (based on the shade generate by the
double skin).
2. Secondly, if the first option is not possible, switch on the light and set the correct
dimmer level to satisfy the constraints. Of course the light will be switch on, if the
policy receive an occupancy greater than one
Otherwise if the internal light is greater than the required one the policy calculates if there
is the possibility to switch off the light, maintaining the constraints verified. If the dimmer
level is greater than one we simply decided to decrease the dimmer level by 1, instead of
switching off directly the light that could create visual discomfort for users.
All these information are published by the policy and received by the actuators module
that sets its configuration. Also the actuators retrieve data from the environment module
(altitude of the sun) in order to set properly the shadowing system position.
Then the actuators module can finally publish the values of the artificial light and of the
shadowing system position updated, ready for the next data coming from the environment.
We can summarize the process in four phases:

As can be seen from the previous figure a control loop is generated. The sensor firstly receives new
external light and sums it up to the old artificial light; the policy controls if the current
configuration is fine or it can be improved (switching on/off light or moving up the
shadowing system). After the cycle sensors-policy-actuators the value taken by the internal
light sensor will be updated.

The input data for our implementation comes from real data taken from 2 website:
1. http://www.sunearthtools.com/
2. http://www.soda-pro.com/web-services/radiation/helioclim-3-for-free
From the first website we downloaded information about altitude and azimuth of the sun
each 15 minutes. As simplification we supposed that each month has the same altitude and
azimuth values taken by the 15th because it was very expensive in terms of time download
data for each day of the year. So we have one file for each month.
Thus from the second file we downloaded data about solar irradiance over the entire 2005
with a periodicity of 15 minutes. In this file there are many other information like
irradiance at the top of atmosphere and we could download them in just one shot.
Files are saved in csv format so they are simply readable by the most part of data analysis
tools. In figure 13 the formats are shown

Using the mean irradiance values retrieved by the second website we found out that these
values were integrated over a time period of 15 minutes. So in order to get the
instantaneous values we divided by the integration time.
Since in our simulator there are 2 illuminance sensors (one for the external light the other
for the overall internal light) we tried to convert irradiance into illuminance. Surfing on the
web we found that is very difficult to transform irradiance into illuminance since a sunspectral-frequency-analysis is needed.
From http://bccp.berkeley.edu/o/Academy/workshop08/08%20PDFs/Inv_Square_Law.pdf
we found an approximate conversion:
and we used this value
in our calculations. These values are then filtered by the double skin’s transmission factors:
the first one equal to 0.91 and the second one equal to 0.49. Finally the illuminance that
enters into the room will depends on the area covered by the shadowing system.


Further, depending on the orientation of our building and on the altitude and azimuth of
the sun, the value of illuminance will be taken only if from our window we can “see” the
sun. In order to afford this problem we decided to filter all those data for which the
azimuth of the sun is lower than the orientation of our building (azimuth equals to 136
degree from the North clockwise direction). At the sunset we don’t have problems because
we have another window in the West position. The light inside will surely depend on the
shadowing system position. So we compute the contribution of the external light inside the
room finding the amount of area uncovered by the shadowing system itself. All the
parameters regarding the building, the room, transmission factors, date and other
simulation parameters are collected in an XML file (Figure 13).
