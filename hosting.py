# NOTES
#

import os
import random
import sys
import time
import re
import fileinput
import pyautogui as kb
from datetime import datetime as dt

kb.PAUSE = 0.4
kb.FAILSAFE = False

launchTime = time.time() + 1

votedPlayers = []
# where 0 = threshold, 1 = target, 2 = time, 3 = type
currentVote = [0, " ", 0, " "]
mapData = {
    "currentMap": "City",
    "currentMode": "Deathmatch"
}
validMaps = ['ucastle', 'utgard', 'castle', 'city', 'training', 'greenscreen', 'cuberace', 'caverace', 'spinrace',
             'forest', 'crystal', 'caves', 'cave', 'underground', 'ucity', 'green', 'arena']

playerOnlineList = {}
playerJoinTime = {}

lastLog = open("Player.log", "w")
lastLog.write("")
lastLog.close()
lastLog = open("./chatlogs/chatlog.txt", "w")
lastLog.write("")
lastLog.close()


def openChat():
    kb.press('y')
    time.sleep(0.3)


def useConsole():
    kb.press('`')
    time.sleep(0.3)


def runTimedEvents():
    global launchTime
    timeNow = time.time()

    # timed events
    # periodic time save
    # if ((timeNow - launchTime) % 30) < 1:
    #    print("Saved player play times.")
    #   for x in playerOnlineList.keys():
    #      updatePlaytimeRecords(x, timeNow)
    # broadcast message
    if ((timeNow - launchTime) % 300) < 1:
        print("Key values for dictionaries - broadcast.")
        print(playerJoinTime.keys())
        print(playerOnlineList.keys())
        if (random.randint(0, 1) == 0):
            openChat()
            kb.write(
                "Join the RAOT OCE discord server today using code yNZPepv5Wz!")
            kb.press('enter')
            openChat()
            kb.write(
                "Looking for a 24/7 host in Asia! Find and DM me on the discord server.")
            kb.press('enter')
            print("Broadcast : 1")
        else:
            openChat()
            kb.write(
                "Join the RAOT OCE discord server today using code yNZPepv5Wz!")
            kb.press('enter')
            openChat()
            kb.write("Don't like the map? Use !votemap (name) to change maps.")
            kb.press('enter')
            print("Broadcast : 2")
    # vote timeout
    if currentVote[1] != " " and timeNow - currentVote[2] >= 30:
        openChat()
        kb.write("Vote timed out.")
        kb.press('enter')
        print("Vote timed out.")
        currentVote[1] = " "
        currentVote[3] = " "
        votedPlayers.clear()
    # end timed events


def updatePlaytimeRecords(key, timeNow):
    fileOverwrite = ""
    for entry in fileinput.input(files="playerTotalTime.txt"):
        entry = entry.split(", ")
        if playerOnlineList[key] == entry[0]:
            authorPlaytime = round(
                (int(timeNow) - playerJoinTime[key]) / 60, 2)
            entry[1] = float(entry[1]) + authorPlaytime
            fileOverwrite += entry[0] + ', ' + str(entry[1]) + '\n'
        else:
            fileOverwrite += entry[0] + ', ' + str(entry[1])
    playerTimeLog = open("playerTotalTime.txt", 'w')
    playerTimeLog.write(fileOverwrite)
    playerTimeLog.close()


def readLineChatLog(line):
    timeNow = time.time()
    msgSource = line[7:10]
    # command handling
    if line.startswith("U"):  # someone joined
        key = line[10:-40]
        EOSid = line[-33:-1]
        if key == "ashphaltHOST":
            playerOnlineList.clear()
            playerJoinTime.clear()
            currentVote[1] = " "
            currentVote[2] = 0
            currentVote[3] = " "
            votedPlayers.clear()
            return
        playerOnlineList.update({key: EOSid})
        playerJoinTime.update({key: int(timeNow)})
        currentVote[0] = int(len(playerOnlineList) / 2) + \
            (len(playerOnlineList) % 2 > 0)
        playerConnectionHistoryLog = open(
            "./chatlogs/playerConnectionHistory.txt", 'a')
        playerConnectionHistoryLog.write(dt.isoformat(
            dt.now()) + " player joined, " + line)
        playerConnectionHistoryLog.close()

        # find if player's first time joining, add for playtime tracking
        found = False
        for entry in fileinput.input(files="./chatlogs/playerTotalTime.txt"):
            entry = entry.split(", ")
            if entry[0] == EOSid:
                found = True
        if not found:
            playerTimeLog = open(
                "./chatlogs/playerTotalTime.txt", 'a')
            playerTimeLog.write(EOSid + ', 0\n')
            playerTimeLog.close()

        # find if player's first time joining, add for alias tracking
        found = False
        for entry in fileinput.input(files="./chatlogs/playerIDs.txt"):
            entry = entry.split(" ")
            if entry[1] == EOSid:
                found = True
        if not found:
            playerIDLog = open(
                "./chatlogs/playerIDs.txt", 'a')
            playerIDLog.write(line)
            playerIDLog.close()

        print("User joined, saved as " + repr(key))
        print("Key values for dictionaries - player joined.")
        print(playerJoinTime.keys())
        print(playerOnlineList.keys())

    elif "(S)" in msgSource and "left" in line:  # someone left
        key = line[12:-18]
        print("User " + key + " left the server")
        playerConnectionHistoryLog = open(
            "./chatlogs/playerConnectionHistory.txt", 'a')
        playerConnectionHistoryLog.write(line)
        playerConnectionHistoryLog.close()
        # updatePlaytimeRecords(key, timeNow)
        print("Key values for dictionaries - player leaving.")
        print(playerJoinTime.keys())
        print(playerOnlineList.keys())
        playerJoinTime.pop(key)
        playerOnlineList.pop(key)
        currentVote[0] = int(len(playerOnlineList) / 2) + \
            (len(playerOnlineList) % 2 > 0)
        if mapData["currentMap"] == "Greenscreen" and len(playerOnlineList) <= 1:
            changeToMap("City")

    elif "(G)" in msgSource:  # someone sent a msg
        msgRaw = line[14:].split(": ", 1)
        # repr returns canonical object, 1:-1 strips quotes "a"
        msgAuthor = repr(msgRaw[0])[1:-1]
        if msgAuthor == "ashphaltHOST":
            return
        msgContent = msgRaw[1].split(" ")
        print(msgRaw)
        # vote initiation
        if ("!votekick" == msgContent[0] or "!votemute" == msgContent[0] or "!votemap" == msgContent[0]) and len(msgContent) > 1:
            # repr stripping, -3 for \n character
            testTarget = repr(msgContent[1])[1:-3]
            if not (testTarget in playerOnlineList) and not (testTarget.lower() in validMaps):
                openChat()
                kb.write("That isn't a valid vote target!")
                kb.press('enter')
                openChat()
                kb.write("For votemap, use one word eg. !votemap training")
                kb.press('enter')
                print("Invalid vote target.")
                return
            elif testTarget == "ashphaltHOST":
                openChat()
                kb.write("nice try bitchass")
                kb.press('enter')
                return
            elif currentVote[3] != " ":  # a vote is in progress
                openChat()
                kb.write(msgAuthor + ", a vote is in progress.")
                kb.press('enter')
                print(msgAuthor + ", a vote is in progress.")
                return

            currentVote[1] = testTarget
            votedPlayers.append(msgAuthor)
            if msgContent[0] == "!votekick":
                openChat()
                kb.write("Vote to kick " +
                         currentVote[1] + " initiated.")
                kb.press('enter')
                currentVote[3] = "kick"
                print("Vote to kick " + currentVote[1] + " initiated.")
            elif msgContent[0] == "!votemute":
                openChat()
                kb.write("Vote to mute " +
                         currentVote[1] + " initiated. ")
                kb.press('enter')
                currentVote[3] = "mute"
                print("Vote to mute " + currentVote[1] + " initiated.")
            elif msgContent[0] == "!votemap":
                openChat()
                kb.write("Vote to change current map to " +
                         currentVote[1] + " initiated.")
                kb.press('enter')
                currentVote[3] = "mapchange"
                print("Vote to change current map to " +
                      currentVote[1] + " initiated.")
                if len(playerOnlineList) <= 1 or playerOnlineList[msgAuthor] == '0002b0b4a80d48da8d45333d71e250ae':
                    openChat()
                    kb.write("Vote to change current map to " +
                             currentVote[1] + " passed - solo vote.")
                    kb.press('enter')
                    changeMapFromVote()
                    time.sleep(3)
                    loadNewMap()
                    currentVote[1] = " "
                    currentVote[2] = 0
                    currentVote[3] = " "
                    votedPlayers.clear()
                    return

            openChat()
            kb.write("Use !voteyes to add your vote.")
            kb.press('enter')
            voteThresholdChat()
            currentVote[2] = timeNow

        # add to an ongoing vote
        elif msgContent[0] == "!voteyes\n" and len(msgContent) == 1:
            if msgAuthor in votedPlayers:
                openChat()
                kb.write("You've already cast your vote!")
                kb.press('enter')
                return
            votedPlayers.append(msgAuthor)
            openChat()
            kb.write("A 'yes' vote was added.")
            kb.press('enter')
            voteThresholdChat()
            print("Vote yes added.")

            if len(votedPlayers) >= currentVote[0]:
                if currentVote[3] == "kick":
                    useConsole()
                    kb.write("kick " + currentVote[1])
                    kb.press("enter")
                    useConsole()
                    openChat()
                    kb.write(currentVote[1] +
                             " was kicked from the server.")
                    kb.press('enter')
                    print(currentVote[1] +
                          " was kicked from the server.")
                elif currentVote[3] == 'mute':
                    useConsole()
                    kb.write("mute " + currentVote[1])
                    kb.press("enter")
                    useConsole()
                    openChat()
                    kb.write(currentVote[1] + " was muted.")
                    kb.press('enter')
                    print(currentVote[1] + " was muted.")
                elif currentVote[3] == 'mapchange':
                    openChat()
                    kb.write("Vote to change map was successful!")
                    kb.press('enter')
                    print("Map changed by vote.")

                    changeMapFromVote()
                    time.sleep(3)
                    loadNewMap()

                currentVote[1] = " "
                currentVote[2] = 0
                currentVote[3] = " "
                votedPlayers.clear()

        # help command
        elif "!help\n" == msgContent[0] and len(msgContent) == 1:
            openChat()
            kb.write(
                "Initiate a vote to kick/mute a player - '!votekick (username)'.")
            kb.press('enter')
            openChat()
            kb.write(
                "Initiate a vote to change the current map - '!votemap (mapname)'.")
            kb.press('enter')
            print("!help was used.")
        # playtime command
        elif "!playtime\n" == msgContent[0] and len(msgContent) == 1:
            openChat()
            kb.write("Rework in progress")
            kb.press('enter')

            #authorPlaytime = (timeNow - playerJoinTime[msgAuthor]) / 60
            # openChat()
            # kb.write(msgAuthor + " has been playing for " +
            #         str(int(authorPlaytime)) + " minutes.")
            # kb.press('enter')
            # print(msgAuthor + " has been playing for " +
            #      str(int(authorPlaytime)) + " minutes.")
            # for entry in fileinput.input(files="./chatlogs/playerTotalTime.txt"):
            #    entry = entry.split(", ")
            #    if entry[0] == playerOnlineList[msgAuthor]:
            #       openChat()
            #      kb.write(msgAuthor + " has played " + str(
            #         round((float(float(entry[1]) + float(authorPlaytime))) / 60, 2)) + " hours across sessions.")
            #    kb.press('enter')
            #   print(msgAuthor + " has played " + str(
            #      round((float(float(entry[1]) + float(authorPlaytime))) / 60, 2)) + " hours across sessions.")

        # end command handling

    # end actions


def voteThresholdChat():
    openChat()
    kb.write(str(len(votedPlayers)) + " / " + str(currentVote[0]))
    kb.press('enter')


def changeMapFromVote():
    changeModeFromPlayers()
    if currentVote[1] == 'ucastle' or currentVote[1] == 'utgard' or currentVote[1] == 'castle':
        changeToMap('Utgard Castle')
    elif currentVote[1] == 'city':
        changeToMap('City')
    elif currentVote[1] == 'training' or currentVote[1] == 'forest':
        changeToMap('Training Forest')
    elif currentVote[1] == 'crystal' or currentVote[1] == 'caves' or currentVote[1] == 'cave':
        changeToMap('Crystal Cave')
    elif currentVote[1] == 'ucity' or currentVote[1] == 'underground':
        changeToMap('Underground City')
    elif currentVote[1] == 'arena':
        changeToMap('Arena')
    elif currentVote[1] == 'greenscreen' or currentVote[1] == 'green':
        changeToMap('Greenscreen')
    elif currentVote[1] == 'cuberace':
        mapData["currentMode"] = "Racing"
        changeToMap('Cuberace')
    elif currentVote[1] == 'spinrace':
        mapData["currentMode"] = "Racing"
        changeToMap('Spinrace')
    elif currentVote[1] == 'caverace':
        mapData["currentMode"] = "Racing"
        changeToMap('Caverace')


def changeMapMenu():
    kb.press('esc')
    y = kb.locateCenterOnScreen(
        './ui elements/changeButton.png', confidence=0.9)
    kb.click(y)
    y = kb.locateCenterOnScreen(
        './ui elements/presetsButton.png', confidence=0.9)
    kb.click(y)

    if mapData["currentMode"] == "Deathmatch":
        y = kb.locateCenterOnScreen(
            './ui elements/presetBaseDM.png', confidence=0.9)
        kb.click(y)
    elif mapData["currentMode"] == "Regicide":
        y = kb.locateCenterOnScreen(
            './ui elements/presetBaseReg.png', confidence=0.9)
        kb.click(y)
    elif mapData["currentMode"] == "Racing":
        y = kb.locateCenterOnScreen(
            './ui elements/presetBaseRacing.png', confidence=0.9)
        kb.click(y)

    y = kb.locateCenterOnScreen(
        './ui elements/presetLoad.png', confidence=0.9)
    kb.click(y)


def changeToMap(mapSelect):
    print("Changing to " + mapSelect)
    mapData["currentMap"] = mapSelect
    openChat()
    kb.write("Now playing " +
             mapData["currentMode"] + " on " + mapSelect.capitalize() + ".")
    kb.press('enter')
    changeMapMenu()

    if mapSelect == 'City':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCitySelected.png', confidence=0.9)
    elif mapSelect == 'Training Forest':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToForest.png', confidence=0.9)
    elif mapSelect == 'Crystal Cave':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToForest.png', confidence=0.9)
        kb.click(x)
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCave.png', confidence=0.9)
    elif mapSelect == 'Underground City':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToForest.png', confidence=0.9)
        kb.click(x)
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCave.png', confidence=0.9)
        kb.click(x)
        x = kb.locateCenterOnScreen(
            './ui elements/changeToUCity.png', confidence=0.9)
    elif mapSelect == 'Arena':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToForest.png', confidence=0.9)
        kb.click(x)
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCave.png', confidence=0.9)
        kb.click(x)
        x = kb.locateCenterOnScreen(
            './ui elements/changeToUCity.png', confidence=0.9)
        kb.click(x)
        x = kb.locateCenterOnScreen(
            './ui elements/changeToArena.png', confidence=0.9)
    elif mapSelect == 'Utgard Castle':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCastle.png', confidence=0.9)
    elif mapSelect == 'Greenscreen':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCastle.png', confidence=0.9)
        kb.click(x)
        x = kb.locateCenterOnScreen(
            './ui elements/changeToGreenscreen.png', confidence=0.9)
    elif mapSelect == 'Cuberace':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCuberace.png', confidence=0.9)
    elif mapSelect == 'Caverace':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToCaverace.png', confidence=0.9)
    elif mapSelect == 'Spinrace':
        x = kb.locateCenterOnScreen(
            './ui elements/changeToSpinrace.png', confidence=0.9)

    kb.click(x)


def loadNewMap():
    x = kb.locateCenterOnScreen('./ui elements/hostButton.png', confidence=0.9)
    kb.click(x)
    time.sleep(15)
    x = kb.locateCenterOnScreen(
        './ui elements/spectateButton.png', confidence=0.9)
    kb.click(x)


def changeModeFromPlayers():
    if mapData["currentMode"] == "Racing":
        mapData["currentMap"] = 'City'
    if len(playerOnlineList) >= 10:
        mapData["currentMode"] = "Regicide"
    else:
        mapData["currentMode"] = "Deathmatch"


def readLinePlayerLog(line):
    if line == '<color=#19A3D4>Match End</color>\n':
        print("Match ended.")
        # actions
        time.sleep(1)

        changeModeFromPlayers()

        if mapData["currentMap"] == 'Utgard Castle':
            changeToMap('City')
        elif mapData["currentMap"] == 'City':
            changeToMap('Training Forest')
        elif mapData["currentMap"] == 'Training Forest':
            changeToMap('Crystal Cave')
        elif mapData["currentMap"] == 'Crystal Cave':
            changeToMap('Underground City')
        elif mapData["currentMap"] == 'Underground City':
            changeToMap('Utgard Castle')
        elif mapData["currentMap"] == 'Greenscreen':
            changeToMap('City')

        time.sleep(6)
        loadNewMap()


def tail(pathPlayerLog, pathChatLog):
    old_size_playerlog = 0
    pos_playerlog = 0
    old_size_chatlog = 0
    pos_chatlog = 0
    while True:
        runTimedEvents()
        # chatlog tailing
        new_size = os.stat(pathChatLog).st_size
        if new_size > old_size_chatlog:
            with open(pathChatLog, "r") as f:
                f.seek(pos_chatlog)
                for line in f:
                    print(line)
                    readLineChatLog(line)
                pos_chatlog = f.tell()
            old_size_chatlog = new_size

        # playerlog tailing
        new_size = os.stat(pathPlayerLog).st_size
        if new_size > old_size_playerlog:
            with open(pathPlayerLog, "r") as f:
                f.seek(pos_playerlog)
                for line in f:
                    print(line)
                    readLinePlayerLog(line)
                pos_playerlog = f.tell()
            old_size_playerlog = new_size

        time.sleep(1)


tail("Player.log", "./chatlogs/chatlog.txt")
