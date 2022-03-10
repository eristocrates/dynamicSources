#!/usr/bin/env python
# -*- coding: utf-8 -*-
# modified from https://github.com/Elektordi/obs-websocket-py/blob/master/samples/switch_scenes.py
import sys 
import time
import logging

# todo/note os, random & shutil are part of failed attempt to randomize source view transition, and need removing.
# waiting on obs websocket 5.x to have access to source view/hide transitions
#import os 
#import random 
#import shutil

from ahk import AHK # https://github.com/spyoungtech/ahk
from ahk.daemon import AHKDaemon # https://github.com/spyoungtech/ahk#ahkdaemon
from enum import Enum, unique # https://docs.python.org/3/library/enum.html
from obswebsocket import obsws, requests # https://github.com/Elektordi/obs-websocket-py
# noqa: E402
@unique
class CameraPosition(Enum):
    TOPLEFT = 0
    BOTTOMLEFT = 1
    BOTTOMRIGHT = 2
# todo/note generate empty data structures, then gui + sign to add to the structures

windowScene = 'CT PC Large Q4' # nested scene with sources to dynamically activate/deactivate
bannerScene = 'LY Banners' # nested scene with other window specific elements I wish to activate
firstActive = True # flag to handle first capture
nonObsNeedsPrint = False # flag to prevent repeat printings of non obs windows in log
cameraPositionsList = ['WC Brio Small Q2', 'WC Brio Small Q3', 'WC Brio Small Q4'] # key human readable description of camera position value name of source for camera position
# todo/note having a dict with human readable key is maybe not as useful to the user? might suck it up and change to a list unless I can justify the added user input
# could likely populate a scenen list here and check them all,
# but i'm currently only implementing on my nested scene for window capture
#stingersPath = 'D:\Streaming\Elements\Stingers\\' # folder with stingers to be randomly applied to view transition
#files = os.listdir(stingersPath)
#destination = "D:\Streaming\Elements\Stingers\Random\stinger.webm"
#comm = [r'C:\Program Files\Unlocker\Unlocker.exe D:\Streaming\Elements\Stingers\Random\stinger.webm /D'] # https://stackoverflow.com/a/1347854

# from ahk
daemon = AHKDaemon(executable_path="E:\\Videos\\Production\\Streaming\\Tools\\AutoHotkey\\AutoHotkey.exe") 
daemon.start()



# from obswebsocket
logging.basicConfig(level=logging.INFO)
sys.path.append('../')
host = "localhost"
port = 4444
password = "" # add your own
ws = obsws(host, port, password)
ws.connect()

try:
    getSceneItemListObject = ws.call(requests.GetSceneItemList(windowScene)) 
    sceneItemList = getSceneItemListObject.getSceneItems()
    print("SceneItemList:", sceneItemList)
    windowList = [source['sourceName'] for source in sceneItemList if source['sourceKind'] == 'group'] # in my obs groups contain relevant window video capture and  window audio capture via https://github.com/bozbez/win-capture-audio
    print("Populated windowList:", windowList)
    windowIsActiveDict = {} # key windowtitle value is window/source/capture active in obs
    for title in windowList:
        windowIsActiveDict[title] = False
    print("Populated windowIsActiveDict", windowIsActiveDict)
    # group names are at very least a substring of expected window title

    getSceneItemListObject = ws.call(requests.GetSceneItemList(bannerScene)) 
    sceneItemList = getSceneItemListObject.getSceneItems()
    bannerList = [source['sourceName'] for source in sceneItemList if source['sourceKind'] == 'image_source'] # images i want in my overlay that correspond to what window is currently active, e.g. guilty gear logo when playing guilty gear
    # image names are the same as group name + " Banner"
    print("Populated bannerList:", bannerList)

    for title in windowList: # https://github.com/spyoungtech/ahk/issues/108 https://stackoverflow.com/a/17500651
        ws.call(requests.SetSceneItemProperties(title,visible=False)) # initially disable all views
    print("Hid all window groups")
    for banner in bannerList: # https://github.com/spyoungtech/ahk/issues/108 https://stackoverflow.com/a/17500651
        #print("Disabling banner for", banner)
        ws.call(requests.SetSceneItemProperties(banner,visible=False)) # initially disable all views
    print("Hid all banners")
    #todo/note essentially the window groups are independent sources but these camera positions are dependent sources, as in each window should have a camera position source associated with it
    #it's like a dependent group of possible scenes where an indepent scene is associated with only a single dependent scene from the group
    #it's important to allow user to set a default/a way to assign all independent scenes to a single dependent scene. In this case by default camera position is bottom Right
    #updates/exceptions can be added afterwards
    ws.call(requests.SetSceneItemProperties(cameraPositionsList[CameraPosition.TOPLEFT.value], visible=False))
    print("Hid top left camera")
    ws.call(requests.SetSceneItemProperties(cameraPositionsList[CameraPosition.BOTTOMLEFT.value], visible=False))
    print("Hid bottom left camera")
    ws.call(requests.SetSceneItemProperties(cameraPositionsList[CameraPosition.BOTTOMRIGHT.value], visible=True))
    print("Activated bottom right camera")
    windowCameraDict = {} # key windowtitle value is window/source/capture active in obs
    for title in windowList:
        windowCameraDict[title] = cameraPositionsList[CameraPosition.BOTTOMRIGHT.value]
    print("Populated windowIsActiveDict", windowIsActiveDict)
    #todo/note make sure this is easy to add to via gui, the user will be here potentially after adding any new source window to capture 
    topLeftTitleList = ['Guilty Gear Strive'] # titles of window groups sources in a list pertaining to their intended camera position
    bottomLeftTitleList = ['RuneLite', 'Vintage Story', 'TagSpaces Desktop'] # titles of window groups sources in a list pertaining to their intended camera position
    for title in topLeftTitleList:
        windowCameraDict[title]=cameraPositionsList[CameraPosition.TOPLEFT.value]
    for title in bottomLeftTitleList:
        windowCameraDict[title]=cameraPositionsList[CameraPosition.BOTTOMLEFT.value]
    print("Populated windowCameraDict", windowCameraDict)



        
    lastTitle = windowList[-1] # initialize to disable last window when enabling new window
    print("Set initial last title to", lastTitle)

    while True:
        time.sleep(1/30) # not sure about which sleep value is best
        winActive = daemon.active_window.title # get active window from ahk
        title = [title for title in windowList if str.encode(title) in winActive] # if a title in obs is a substring of the active window
        if title != []: # if a title in obs is a substring of the active window
            title = title[0]
            if (firstActive or not windowIsActiveDict[title]) and str.encode(title) in winActive: # if active window title shares a title with a group in obs, enable it. Also checks for first time to set up checking via dictionary afterwards
                # not windowdict prevents activating an already active window
                print()
                print(winActive, "found as the window for the OBS source", title)
                ws.call(requests.SetSceneItemProperties(title, windowScene, visible=True))
                print("Enabled window for", title)
                ws.call(requests.SetSceneItemProperties(title + " Banner", bannerScene, visible=True))
                print("Enabled banner for", title)
                if windowCameraDict[title] != windowCameraDict[lastTitle]: # enables new camera only if the camera position would change 
                    ws.call(requests.SetSceneItemProperties(windowCameraDict[title], visible=True)) # todo/note all 3 potential camera sourcese are in my regular active scene, but it may be worth gathering user input on where they expect their camera sources to be 
                    print("Enabled camera for", title)
                windowIsActiveDict[title] = True
                print("Set dictionary to true for", title)
                print("Active window:", winActive)
                nonObsNeedsPrint = True

                print("\nLast title currently", lastTitle,"\n")

            if not str.encode(lastTitle) in winActive and lastTitle != title: # if last title is no longer active, disable it
                # lastTitle != title prevent disabling an already active source when going from a source to a non obs source window back to the same source
                #source = os.path.join(stingersPath + random.choice(files)) # https://www.geeksforgeeks.org/python-shutil-copy-method/
                # reset view transition stinger before disabling to be ready for new title when it is enabled 
                #os.chmod(destination, 0o777) # 
                #os.remove(destination)
                #subprocess.run(comm, shell=True) # Delete stinger file via Unlocker subprocess # https://stackoverflow.com/questions/40492351/using-subprocess-run-to-run-a-process-on-windowshttps://stackoverflow.com/a/40492767
                #shutil.copy(source, destination) 
                print()

                ws.call(requests.SetSceneItemProperties(lastTitle, windowScene, visible=False))
                print("Disabled window for", lastTitle)
                ws.call(requests.SetSceneItemProperties(lastTitle + " Banner", bannerScene, visible=False))
                print("Disabled banner for", lastTitle)
                if windowCameraDict[title] != windowCameraDict[lastTitle]: # disables old camera only if the camera position would change 
                    ws.call(requests.SetSceneItemProperties(windowCameraDict[lastTitle], visible=False)) 
                    print("Disabled camera for", lastTitle)
                windowIsActiveDict[lastTitle] = False
                print("Set dictionary to false for", title)
                lastTitle = title
                if  firstActive: 
                    firstActive = False 
                    print("For the first run, set last title to", lastTitle)
                else: 
                    print("Set last title to", lastTitle)
        else:
            if nonObsNeedsPrint: 
                print()
                print(winActive, "not found as the window for any OBS source")
                nonObsNeedsPrint = False
        
        #for title in windowList: # checks if any # https://github.com/spyoungtech/ahk/issues/108 https://stackoverflow.com/a/17500651
        #    if [str.encode(title) for title in windowList if str.encode(title) in winActive] != []: # if a title in obs is a substring of the active window
            

except KeyboardInterrupt:
    pass

ws.disconnect()
daemon.stop()
