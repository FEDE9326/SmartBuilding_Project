'''
Created on 12 nov 2016

@author: federico
'''

import mosquitto
import json
import threading
import numpy as np
import xml.etree.ElementTree as ET

broker_ip="127.0.0.1"
steps=0.5
sun_elevation=0.0
artificial_light=0.1
shadow_position=0.1
light_status=0
dec_step_needed=0
dimmer_level=0

file_name='actuator.csv'

#DECISION NEVER HAPPEN THAT THE SH SYSTEM IS COMPLETELY CLOSE!

def on_connect(client,userdata,rc):
    print ("connected with result code"+str(rc)+": "+client._client_id)
    client.subscribe("policy/commands", 2)
    client.subscribe("environment/sun_light",2)
    client.subscribe("command/end",2)

    
def on_message(client,userdata,msg):
    
    global light_status,dec_step_need,dimmer_level,sun_elevation
    
    jsonfile=json.loads(msg.payload)
    
    if msg.topic=="environment/sun_light":
    
        sun_elevation=float(jsonfile["elevation"])
        
    elif msg.topic=="policy/commands":
        
        light_status=jsonfile["light_status"]
            
        dec_step_need=jsonfile["shadowing_system_step"]
        
        data={}
        data["time"]=jsonfile["time"]
        
        setShadowingSystemPosition()
        
        data["position"]=shadow_position
        
        if jsonfile["side"]=="SW":
            data["area"]=round((1-shadow_position*steps*y/(y*3)),2)
        elif jsonfile["side"]=="W":
            data["area"]=round((1-shadow_position*steps*(y/3)/((y/3)*3)),2)
            
        data["light_status"]=light_status
        
        #SEt dimmer level and artificial light
        if light_status==1:
            dimmer_level=jsonfile["dimmer_level"]
            if dimmer_level==1:
                artificial_light=step1*n_lights/(x*y)
                data["artificial_light"]=artificial_light
            elif dimmer_level==2:
                artificial_light=step2*n_lights/(x*y)
                data["artificial_light"]=artificial_light
            else:
                artificial_light=step3*n_lights/(x*y)
                data["artificial_light"]=artificial_light
        else:
            dimmer_level=0
            artificial_light=0
            data["artificial_light"]=artificial_light
        
        jsonfile2=json.dumps(data)
        
        t=threading.Thread(target=send_data,args=(client,jsonfile2,))
        t.start()
        
        #Writing on file
        output=open(file_name,"a")
        output.write(str(jsonfile["time"]) +"," + str(shadow_position)+","+str(dimmer_level)+"\n")
        output.close()
        
    elif msg.topic=="command/end":
        
        if jsonfile["command"]==1:
            client.disconnect()
             
def send_data(client,jsonfile2):
    client.publish("actuators/control",jsonfile2, qos=2)
    
def on_disconnect(client,userdata,rc):
    print "Actuators disconnecting"
    
#Update the shadowing system position
def setShadowingSystemPosition():
    
    global sun_elevation,dec_step_needed,steps,shadow_position
    
    if dec_step_needed==0:
        shadow_position=np.ceil(np.tan(sun_elevation*2*np.pi/360)/steps)+1
        if shadow_position>=6:
            shadow_position=5
    else:
        #Possibility to move up by 1 step to add internal light inside
        shadow_position=np.ceil(np.tan(sun_elevation*2*np.pi/360)/steps)
        if shadow_position>=6:
            shadow_position=5
    
if __name__ == '__main__':
    
    
    client=mosquitto.Mosquitto("actuators")
    client.on_connect=on_connect
    client.on_message=on_message
    client.on_disconnect=on_disconnect
    
    client.connect(broker_ip, port=1883, keepalive=60, bind_address="") 
    
    e=ET.parse("config.xml").getroot()
    
    buil=e.find("Building")
    
    rooms=buil.find("Rooms")
    
    lux_min=float(rooms.get("LUX"))
    n_lights=float(rooms.get("NumberOfLights"))
    step1=float(rooms.get("Dimmer1Step"))
    step2=float(rooms.get("Dimmer2Step"))
    step3=float(rooms.get("Dimmer3Step"))
    x=float(rooms.get("x"))
    y=float(rooms.get("y"))
       
    client.loop_forever()
    
    