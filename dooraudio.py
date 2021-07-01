# -*- coding: utf-8 -*-
import paho.mqtt.subscribe as subscribe 
import paho.mqtt.client as mqtt
import json
import pygame
import credentials
import glob
import random
import time
import os
mqttc=mqtt.Client()
print("cwd: %s" % os.getcwd())
username = credentials.username # str(raw_input("username: "))
password = credentials.password #str(raw_input("password: "))
mqttc.username_pw_set(username=username,password=password)

pygame.mixer.init() 
pygame.mixer.set_num_channels(2)



global switch_state 
global base_topic_switch
global laughingtracks, musiclist
switch_state = "OFF"

base_topic_switch = "homeassistant/switch/themesong"
doortopic = "zigbee2mqtt/door_sensor_1"
config_switch = u'{"~": "%s", "name": "themesong","stat_t": "~/state", "cmd_t": "~/set"}' % base_topic_switch
subtopics = [(base_topic_switch+"/#",1),(doortopic,1)]



def find_audio_files(subfolder):
    extensions = ["wav"] 
    filelist=[]
    for ext in extensions:
        filelist = filelist + glob.glob("./"+subfolder+"/*."+ext)

    return filelist

laughingtracks=find_audio_files("laughingtracks")

musiclist=find_audio_files("music")



def on_message(mqttc, obj, msg):
    global switch_state, laughingtracks, musiclist
    # try:
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload)+ "\n retain: %d" % msg.retain)
    if msg.topic == doortopic:
        payload = json.loads(msg.payload)
        if not(payload['contact']):

            laughingtracks=find_audio_files("laughingtracks")
            musiclist=find_audio_files("music")
            if switch_state == "ON":
                play_audio()
    if msg.topic == base_topic_switch+"/set":
        switch_state = (msg.payload).decode("utf-8")
        print("Switch state: %s" % switch_state)
        update_switch(switch_state)
    if msg.topic == base_topic_switch+"/state": # to update retained
        switch_state = (msg.payload).decode("utf-8")
        print("Switch state: %s" % switch_state)
        if switch_state == "OFF":
            pygame.mixer.pause()
            print("audio paused")
    # except:
    #     print("error\n")

def update_switch(state):
    global base_topic_switch
    mqttc.publish(base_topic_switch+"/state",state,qos=1,retain=True)


def on_publish(mqttc, obj, mid):
    print("publish: \n")
    print("mid: " + str(mid))





def play_audio():
    global laughingtracks, musiclist

    print("playing audio")
    # if not(pygame.mixer.music.get_busy()):
    rand=random.randint(0,len(laughingtracks)-1) # select random laughing track
    laugh=laughingtracks[rand]
    rand=random.randint(0,len(musiclist)-1) # select random music track
    music=musiclist[rand]
    print("playing %s" % music)
    pygame.mixer.Channel(0).play(pygame.mixer.Sound(music.replace("\\","/")))
    # time.sleep(5)

    
    # print("playing %s" % laugh)
    # pygame.mixer.Channel(1).play(pygame.mixer.Sound(laugh))
    
    while pygame.mixer.Channel(0).get_busy():
        while pygame.mixer.Channel(1).get_busy():
            continue
        
        time.sleep(5)
        if pygame.mixer.Channel(0).get_busy() and not(pygame.mixer.Channel(1).get_busy()):
           
            rand=random.randint(0,len(laughingtracks)-1) # select random laughing track
            laugh=laughingtracks[rand]
            print("playing %s" % laugh)
            pygame.mixer.Channel(0).set_volume(0.4)
            pygame.mixer.Channel(1).play(pygame.mixer.Sound(laugh.replace("\\","/")))
        
        # while pygame.mixer.music.get_busy() == True:
        #     continue
        continue
    print("audio ended")
        

def on_connect(mqttc, obj, flags, rc):
    print("rc: ", str(rc))
    mqttc.publish(base_topic_switch+"/config",config_switch,retain=True)
    play_audio()
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

mqttc.on_message = on_message
mqttc.on_connect = on_connect 
mqttc.on_subscribe = on_subscribe 
mqttc.on_publish = on_publish

mqttc.connect(host="192.168.178.44",port=1883)
mqttc.subscribe(subtopics)
mqttc.loop_forever()