'''
Created on 12 nov 2016

@author: federico
'''
import time
import mosquitto
import json
import xml.etree.ElementTree as ET
import csv
import numpy as np


from itertools import islice
from Sensors import conversion_lux_wm2

broker_ip="127.0.0.1"
power_file="environment.csv"

def on_connect(client,userdata,rc):
    print ("connected with result code"+str(rc)+": "+client._client_id)

def getSolarLight():
    
    '''returns a dictionary of the power over the selected day: 
       diz(time_in_decimal)=irradiance all in float
    '''
    
    e=ET.parse("config.xml").getroot()
    
    start_date=e.get("StartDate")
    start_time=e.get("StartTime")
    
    d,m,y=start_date.split("/")
    h=start_time.split(":")[0]
    
    try:
        f=open("Data/TurinSolarPower.csv",'rb')
    except:
        print "Error in opening the file Power"
        
    try:
        reader=csv.reader(f,delimiter=',')
    except:
        print "Error in parsing file Power"
    
    diz={}
    
    for row in islice(reader,22,None):

        if (row[0]==str('2004') and row[1]==m and row[2]==d and float(row[3])>float(h)):
            diz[float(row[3])]=float(row[4])
            
    
    return diz
            
def getSolarPosition():
    
    '''returns a dictionary of the position of the sun over the selected day: 
       diz(time_in_decimal)=elev,azimuth all in float
    '''
    
    e=ET.parse("config.xml").getroot()
    
    start_date=e.get("StartDate")
    start_time=e.get("StartTime")
    
    m=start_date.split("/")[1]
    h=start_time.split(":")[0]
    
    filename="Data/"+m+".csv"
    
    try:
        f=open(filename,'rb')
    except:
        print "Error in opening the file Position"
        
    try:
        reader=csv.reader(f,delimiter=',')
    except:
        print "Error in parsing file Power"
    
    diz={}
    for row in islice(reader,4,None):
        
        h_f,m,s=row[0].split(":")
        if float(h_f)>=float(h):
            h_float=round(float(h_f)+float(m)/60,2) #in decimal
    
            diz[h_float]=[float(row[1]),float(row[2])]
            
    f.close()
    
    return diz

if __name__ == '__main__':
    
    
    client=mosquitto.Mosquitto("Environment")
    client.on_connect=on_connect
  
    client.connect(broker_ip, port=1883, keepalive=60, bind_address="") 
    client.loop_start()
    
    #Getting configurations from XML file
    e=ET.parse("config.xml").getroot()
    
    simulation_clock=float(e.get("SimulationClock"))
    frequency_data=float(e.get("FrequencyData"))
    start_time=float(e.get("StartTime").split(":")[0])
    end_time=float(e.get("OfficeEndTime").split(":")[0])
    
    buil=e.find("Building")    
    orientation_EAST=float(buil.get("OrientationEast"))
    orientation_WEST=float(buil.get("OrientationWest"))
    
    wind=buil.find("Window")
    w_height=float(wind.get("Height"))
    w_length=float(wind.get("Width"))
    ext_diff=float(wind.get("ExternalDiffusion"))
    int_diff=float(wind.get("InternalDiffusion"))
    
    #Extracting solar data from files 
    solar_light=getSolarLight()
    solar_position=getSolarPosition()
    
    discrete_time=start_time
    
    #Starting the simulation
    while(float(discrete_time)<end_time):
        
        try:
            power_first=solar_light[float(discrete_time)]
        except:
            power_first=0
        try:
            position=solar_position[discrete_time] #list
        except:
            position=[]
            position.append(0)
            position.append(None)
        
        data={}
        data["time"]=discrete_time
        
        if position[1]>orientation_EAST:
        # Sending data if the azimuth is greater than the orientation of the building
            
            data["irradiance"]=power_first/(frequency_data*100)
            
            #Supposition: continuous luminance flow from one side to the other: the difference is just the area of the window
            if position[1]<orientation_WEST:
                #data from SW window
                data["side"]="SW"
                data["lux_no_DSSW"]=(power_first*int_diff*ext_diff/(frequency_data*100))/conversion_lux_wm2
                data["lux_with_shadow"]=(power_first*(w_length*w_height-np.tan(position[0]*2*np.pi/360)*w_length)/((frequency_data*100)*(w_length*w_height)))/conversion_lux_wm2
                data["irradiance_with_filtering"]=power_first*int_diff*ext_diff*(w_length*w_height-np.tan(position[0]*2*np.pi/360)*w_length)/((frequency_data*100)*(w_length*w_height))
            else:
                #data from West side window
                data["side"]="W"
                data["lux_no_DSSW"]=(power_first*int_diff*ext_diff/(frequency_data*100))/conversion_lux_wm2
                data["lux_with_shadow"]=(power_first*((w_length/3)*w_height-np.tan(position[0]*2*np.pi/360)*(w_length/3))/((frequency_data*100)*((w_length/3)*w_height)))/conversion_lux_wm2
                data["irradiance_with_filtering"]=power_first*int_diff*ext_diff*((w_length/3)*w_height-np.tan(position[0]*2*np.pi/360)*(w_length/3))/((frequency_data*100)*((w_length/3)*w_height))
        else:
        # All values equal to 0
        
            data["irradiance"]=0
            data["irradiance_with_filtering"]=0
            data["lux_with_shadow"]=0
            data["lux_no_DSSW"]=0
            data["side"]=0
            
        if position[0]>0:
        # JUst a control because from data if the elevation is under the horizon there are negative values
            data["elevation"]=position[0]
        else:
            data["elevation"]=0
        
        data["azimuth"]=position[1]
        
        jsonfile=json.dumps(data)
        print "sending at "+str(data["time"])+" "+str(data["lux_no_DSSW"])+"\n"
        
        #Publishing of data
        client.publish("environment/sun_light",jsonfile, qos=2)
        
        #WRITING RESULTS ON FILE
        output=open(power_file,"a")
        output.write(str(discrete_time)+","+str(data["irradiance"])+","+str(data["lux_with_shadow"]*conversion_lux_wm2)+","+str(data["irradiance_with_filtering"])+","+str(data["elevation"])+"\n")
        output.close()
        
        time.sleep(simulation_clock)
        
        discrete_time+=frequency_data*100/60
    
    time.sleep(2)
    
    #Sending off command to kill all the clients 
    data={}
    data["command"]=1
    jsonfile=json.dumps(data)
    client.publish("command/end",jsonfile,qos=2)
        
    client.loop_stop()
    
