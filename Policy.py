'''
Created on 12 nov 2016

@author: federico
'''

import mosquitto
import json
import threading
import xml.etree.ElementTree as ET


broker_ip="127.0.0.1"

shadow_position=0
light_value=0
dimmer_level=0
light_status=0
lux_min=0.0
n_lights=0
step1=0.0
step2=0.0
step3=0.0
x=0
y=0
number_of_people=0


def on_connect(client,userdata,rc):
    print ("connected with result code"+str(rc)+": "+client._client_id)
    client.subscribe("sensors/light_value", 2)
    client.subscribe("command/end",2)

def on_message(client,userdata,msg):
    
    jsonfile=json.loads(msg.payload)
    
    if msg.topic=="sensors/light_value":
        
        global light_value,dimmer_level,light_status,lux_min,number_of_people,step1,step2,y
        
        light_value=float(jsonfile["light_value"])
        external_light=float(jsonfile["external_light"])
        number_of_people=int(jsonfile["occupancy"])
        side=jsonfile["side"]
        data={}
        data["time"]=jsonfile["time"]
        data["side"]=side
        
        #Changing in the size of the window
        if side=="W":
            y=y/3
        
        if number_of_people>0:
            
            print str(jsonfile["time"]) + " "+str(light_value)+ " "+str(external_light)+"\n"
            
            if light_value<lux_min:
                #Light lower than the threshold
                print "light_lower than 500 at time"+ str(jsonfile["time"])+ " value="+str(jsonfile["light_value"])
                if (external_light+external_light*(1/6))>=lux_min:
                    #you can move up the shadowing system by 1 step
                    print "possible open the ss"
                    data["shadowing_system_step"]=1 #means you have to get up the shadowing system by 1 step
                    data["light_status"]=0
                    dimmer_level=0
                    light_status=0
                    data["dimmer_level"]=dimmer_level
                    
                else:
                    data["shadowing_system_step"]=0 #no possibility to open the shadowing system
                    if light_status==0:
                        #LIGHT IS OFF: FIND WHICH STEP IS THE BEST
                        light_status=1
                        data["light_status"]=light_status
                        print "SS set to 1"
                        if light_value+step1*n_lights/(x*y)>=lux_min:
                            dimmer_level=1
                        elif light_value+step2*n_lights/(x*y)>=lux_min:
                            print "SS set to 2"
                            dimmer_level=2
                        else:
                            dimmer_level=3
                            
                        data["dimmer_level"]=dimmer_level
                        
                    else:
                        #LIGHT ALREADY SWITCH ON: INCREASE DIMMER STEP BY 1
                        data["light_status"]=light_status
                        print "ligh already switch on dimmer++"
                        dimmer_level+=1
                        data["dimmer_level"]=dimmer_level
                        
                        
            else:
                #light_value>500
                if dimmer_level==0: 
                    #It means only outside light: in addition the shadowing system can advance by 1 one step
                    data["shadowing_system_step"]=0
                    data["light_status"]=0
                    dimmer_level=0
                    light_status=0
                    data["dimmer_level"]=dimmer_level
                    
                elif dimmer_level==1 and (light_value-step1*n_lights/(x*y))>=lux_min:
                    #It means dimmer=1 but there is enough outside light to match the constraint
                    data["shadowing_system_step"]=0
                    light_status=0
                    data["light_status"]=light_status
                    dimmer_level=0
                    data["dimmer_level"]=dimmer_level
                    
                elif dimmer_level==2 and light_value-(step2-step1)*n_lights/(x*y)>=lux_min:
                    #It means you can decrease by 1 the dimmer level
                    data["shadowing_system_step"]=0
                    light_status=1
                    data["light_status"]=light_status
                    dimmer_level=1
                    data["dimmer_level"]=dimmer_level
                else:
                    #Nothing take values from the last iteration
                    data["shadowing_system_step"]=0
                    data["light_status"]=light_status
                    data["dimmer_level"]=dimmer_level
        else:
            #NOBODY INSIDE THE ROOM NO NEED OF LIGHTS->INSTEAD THE SH SYSTEM CONTINUE ITS SCHEDULE
            data["shadowing_system_step"]=0
            light_status=0
            data["light_status"]=light_status
            dimmer_level=0
            data["dimmer_level"]=dimmer_level
                            
        jsonfile2=json.dumps(data)
        t=threading.Thread(target=send_data,args=(client,jsonfile2,))
        t.start()
        
    elif msg.topic=="command/end":
        if jsonfile["command"]==1:
            t=threading.Thread(target=send_data_end,args=(client,jsonfile,))
            t.start()

def send_data_end(client,jsonfile):
    client.publish("command/end",json.dumps(jsonfile),qos=2)
    client.disconnect() 

def on_disconnect(client,userdata,rc):
    print "Policy diconnecting"
   
def send_data(client,jsonfile2):
    client.publish("policy/commands",jsonfile2, qos=2) 
    print jsonfile2      
        

if __name__ == '__main__':
    
    client=mosquitto.Mosquitto("policy")
    client.on_connect=on_connect
    client.on_message=on_message
    client.on_disconnect=on_disconnect
    
    client.connect(broker_ip, port=1883, keepalive=60, bind_address="") 
    
    e=ET.parse("config.xml").getroot()
    
    simulation_clock=float(e.get("SimulationClock"))
    frequency_data=float(e.get("FrequencyData"))
    start_time=float(e.get("StartTime").split(":")[0])
    
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
    