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
# current_vote_dict = [0, " ", 0, " "]

current_vote_dict = {
    "threshold": 0,
    "target": " ",
    "time_start": 0,
    "type": " "
}

mapData = {
    "currentMap": "City",
    "currentMode": "Deathmatch"
}
validMaps = ['ucastle', 'utgard', 'castle', 'city', 'training', 'greenscreen', 'cuberace', 'caverace', 'spinrace',
             'forest', 'crystal', 'caves', 'cave', 'underground', 'ucity', 'green', 'arena']

playerOnlineList = {}
playerJoinTime = {}

# reset Player.log, chatlog.txt
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


def writeMessage(message):
    openChat()
    kb.write(message)
    kb.press('enter')


# run all timed events using time since launch
def runTimedEvents():
    global launchTime
    time_now = time.time()

    # timed events
    # periodic time save
    # if ((timeNow - launchTime) % 30) < 1:
    #    print("Saved player play times.")
    #   for x in playerOnlineList.keys():
    #      updatePlaytimeRecords(x, timeNow)

    # broadcast message every ~6 minutes
    if ((time_now - launchTime) % 360) < 1:
        # print("Key values for dictionaries - broadcast.")
        # print(playerJoinTime.keys())
        # print(playerOnlineList.keys())
        writeMessage("Join the RAOT OCE discord server today using code yNZPepv5Wz!")
        writeMessage("Don't like the map? Use !votemap (name) to change maps.")

    # timeout an ongoing vote if it has been >30 seconds
    if current_vote_dict["target"] != " " and time_now - current_vote_dict["time_start"] >= 30:
        writeMessage("Vote timed out.")
        print("Vote timed out.")
        current_vote_dict["target"] = " "
        current_vote_dict["type"] = " "
        votedPlayers.clear()


# update total play time record of a player using their ID and parameter time
# if player unknown, create a new record for them
def updatePlaytimeRecords(key, time_now):
    file_overwrite = ""
    for entry in fileinput.input(files="playerTotalTime.txt"):
        entry = entry.split(", ")
        if playerOnlineList[key] == entry[0]:
            author_playtime = round((int(time_now) - playerJoinTime[key]) / 60, 2)
            entry[1] = float(entry[1]) + author_playtime
            file_overwrite += entry[0] + ', ' + str(entry[1]) + '\n'
        else:
            file_overwrite += entry[0] + ', ' + str(entry[1])
    player_time_log = open("playerTotalTime.txt", 'w')
    player_time_log.write(file_overwrite)
    player_time_log.close()


def readLineChatLog(line):
    time_now = time.time()
    msg_source = line[7:10]

    # command handling
    if line.startswith("U"):  # someone joined
        key = line[10:-40]
        eos_id = line[-33:-1]

        if key == "ashphaltHOST": # the case where the server just started
            playerOnlineList.clear()
            playerJoinTime.clear()
            current_vote_dict["target"] = " "
            current_vote_dict["time_start"] = 0
            current_vote_dict["type"] = " "
            votedPlayers.clear()
            return

        # update list of players, log the joining player's connect time, update voting threshold
        playerOnlineList.update({key: eos_id})
        playerJoinTime.update({key: int(time_now)})
        current_vote_dict["threshold"] = int(len(playerOnlineList) / 2) + (len(playerOnlineList) % 2 > 0)

        # log player connect event
        player_connection_history_log = open("./chatlogs/playerConnectionHistory.txt", 'a')
        player_connection_history_log.write(dt.isoformat(dt.now()) + " player joined, " + line)
        player_connection_history_log.close()

        # find if player's first time joining, add for playtime tracking
        found = False
        for entry in fileinput.input(files="./chatlogs/playerTotalTime.txt"):
            entry = entry.split(", ")
            if entry[0] == eos_id:
                found = True
        if not found:
            player_time_log = open("./chatlogs/playerTotalTime.txt", 'a')
            player_time_log.write(eos_id + ', 0\n')
            player_time_log.close()

        # find if player's first time joining, add for alias tracking
        found = False
        for entry in fileinput.input(files="./chatlogs/playerIDs.txt"):
            entry = entry.split(" ")
            if entry[1] == eos_id:
                found = True
        if not found:
            player_id_log = open("./chatlogs/playerIDs.txt", 'a')
            player_id_log.write(line)
            player_id_log.close()

        print("User joined, saved as " + repr(key))
        print("Key values for dictionaries - player joined.")
        print(playerJoinTime.keys())
        print(playerOnlineList.keys())

    elif "(S)" in msg_source and "left" in line:  # someone left
        key = line[12:-18]
        print("User " + key + " left the server")
        player_connection_history_log = open("./chatlogs/playerConnectionHistory.txt", 'a')
        player_connection_history_log.write(line)
        player_connection_history_log.close()
        # updatePlaytimeRecords(key, time_now)
        print("Key values for dictionaries - player leaving.")
        print(playerJoinTime.keys())
        print(playerOnlineList.keys())
        playerJoinTime.pop(key)
        playerOnlineList.pop(key)
        current_vote_dict["threshold"] = int(len(playerOnlineList) / 2) + (len(playerOnlineList) % 2 > 0)

        # if there are no players left, it's probably because we're on greenscreen...
        if mapData["currentMap"] == "Greenscreen" and len(playerOnlineList) <= 1:
            changeToMap("City")

    elif "(G)" in msg_source:  # someone sent a msg
        raw_msg = line[14:].split(": ", 1)
        # repr to extract string, 1:-1 strips quotes "a"
        msg_author = repr(raw_msg[0])[1:-1]
        if msg_author == "ashphaltHOST":
            return
        msg_content = raw_msg[1].split(" ")
        print(raw_msg)

        # vote initiation
        if ("!votekick" == msg_content[0] or "!votemute" == msg_content[0] or "!votemap" == msg_content[0]) and len(msg_content) > 1:
            # repr stripping, -3 for \n character
            testTarget = repr(msg_content[1])[1:-3]
            if not (testTarget in playerOnlineList) and not (testTarget.lower() in validMaps):
                writeMessage("That isn't a valid vote target!")
                writeMessage("For votemap, use one word eg. !votemap training")
                print("Invalid vote target.")
                return
            elif testTarget == "ashphaltHOST":
                writeMessage("nice try bitchass")
                return
            elif current_vote_dict["type"] != " ":  # a vote is in progress
                writeMessage(msg_author + ", a vote is in progress.")
                print(msg_author + ", a vote is in progress.")
                return

            current_vote_dict["target"] = testTarget
            votedPlayers.append(msg_author)
            if msg_content[0] == "!votekick":
                openChat()
                kb.write("Vote to kick " +
                         current_vote_dict["target"] + " initiated.")
                kb.press('enter')
                current_vote_dict["type"] = "kick"
                print("Vote to kick " + current_vote_dict["target"] + " initiated.")
            elif msg_content[0] == "!votemute":
                openChat()
                kb.write("Vote to mute " +
                         current_vote_dict["target"] + " initiated. ")
                kb.press('enter')
                current_vote_dict["type"] = "mute"
                print("Vote to mute " + current_vote_dict["target"] + " initiated.")
            elif msg_content[0] == "!votemap":
                openChat()
                kb.write("Vote to change current map to " +
                         current_vote_dict["target"] + " initiated.")
                kb.press('enter')
                current_vote_dict["type"] = "mapchange"
                print("Vote to change current map to " +
                      current_vote_dict["target"] + " initiated.")
                if len(playerOnlineList) <= 1 or playerOnlineList[msg_author] == '0002b0b4a80d48da8d45333d71e250ae':
                    openChat()
                    kb.write("Vote to change current map to " +
                             current_vote_dict["target"] + " passed - solo vote.")
                    kb.press('enter')
                    changeMapFromVote()
                    time.sleep(3)
                    loadNewMap()
                    current_vote_dict["target"] = " "
                    current_vote_dict["time_start"] = 0
                    current_vote_dict["type"] = " "
                    votedPlayers.clear()
                    return

            openChat()
            kb.write("Use !voteyes to add your vote.")
            kb.press('enter')
            voteThresholdChat()
            current_vote_dict["time_start"] = time_now

        # add to an ongoing vote
        elif msg_content[0] == "!voteyes\n" and len(msg_content) == 1:
            if msg_author in votedPlayers:
                openChat()
                kb.write("You've already cast your vote!")
                kb.press('enter')
                return
            votedPlayers.append(msg_author)
            openChat()
            kb.write("A 'yes' vote was added.")
            kb.press('enter')
            voteThresholdChat()
            print("Vote yes added.")

            if len(votedPlayers) >= current_vote_dict["threshold"]:
                if current_vote_dict["type"] == "kick":
                    useConsole()
                    kb.write("kick " + current_vote_dict["target"])
                    kb.press("enter")
                    useConsole()
                    openChat()
                    kb.write(current_vote_dict["target"] +
                             " was kicked from the server.")
                    kb.press('enter')
                    print(current_vote_dict["target"] +
                          " was kicked from the server.")
                elif current_vote_dict["type"] == 'mute':
                    useConsole()
                    kb.write("mute " + current_vote_dict["target"])
                    kb.press("enter")
                    useConsole()
                    openChat()
                    kb.write(current_vote_dict["target"] + " was muted.")
                    kb.press('enter')
                    print(current_vote_dict["target"] + " was muted.")
                elif current_vote_dict["type"] == 'mapchange':
                    openChat()
                    kb.write("Vote to change map was successful!")
                    kb.press('enter')
                    print("Map changed by vote.")

                    changeMapFromVote()
                    time.sleep(3)
                    loadNewMap()

                current_vote_dict["target"] = " "
                current_vote_dict["time_start"] = 0
                current_vote_dict["type"] = " "
                votedPlayers.clear()

        # help command
        elif "!help\n" == msg_content[0] and len(msg_content) == 1:
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
        elif "!playtime\n" == msg_content[0] and len(msg_content) == 1:
            openChat()
            kb.write("Rework in progress")
            kb.press('enter')

            # authorPlaytime = (time_now - playerJoinTime[msg_author]) / 60
            # openChat()
            # kb.write(msg_author + " has been playing for " +
            #         str(int(authorPlaytime)) + " minutes.")
            # kb.press('enter')
            # print(msg_author + " has been playing for " +
            #      str(int(authorPlaytime)) + " minutes.")
            # for entry in fileinput.input(files="./chatlogs/playerTotalTime.txt"):
            #    entry = entry.split(", ")
            #    if entry[0] == playerOnlineList[msg_author]:
            #       openChat()
            #      kb.write(msg_author + " has played " + str(
            #         round((float(float(entry[1]) + float(authorPlaytime))) / 60, 2)) + " hours across sessions.")
            #    kb.press('enter')
            #   print(msg_author + " has played " + str(
            #      round((float(float(entry[1]) + float(authorPlaytime))) / 60, 2)) + " hours across sessions.")

        # end command handling

    # end actions


def voteThresholdChat():
    openChat()
    kb.write(str(len(votedPlayers)) + " / " + str(current_vote_dict["threshold"]))
    kb.press('enter')


def changeMapFromVote():
    changeModeFromPlayers()
    match current_vote_dict["threshold"]:
        case "ucastle" | "utgard" | "castle":
            changeToMap('Utgard Castle')
        case "city":
            changeToMap('City')
        case "training" | "forest":
            changeToMap('Training Forest')
        case "crystal" | "caves" | "cave":
            changeToMap('Crystal Cave')
        case "ucity" | "underground":
            changeToMap('Underground City')
        case "arena":
            changeToMap('Arena')
        case "greenscreen" | "green":
            changeToMap('Greenscreen')
        case "cuberace":
            mapData["currentMode"] = "Racing"
            changeToMap('Cuberace')
        case "spinrace":
            mapData["currentMode"] = "Racing"
            changeToMap('Spinrace')
        case "caverace":
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

#
# if racing was just played, switch to another gamemode
#
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
        time.sleep(1)

        changeModeFromPlayers()

        match mapData["currentMap"]:
            case "Utgard Castle":
                changeToMap('City')
            case "City":
                changeToMap('Training Forest')
            case "Training Forest":
                changeToMap('Crystal Cave')
            case "Crystal Cave":
                changeToMap('Underground City')
            case "Underground City":
                changeToMap('Utgard Castle')
            case "Greenscreen":
                changeToMap('City')

        time.sleep(6)
        loadNewMap()


def tail(player_log_path, chat_log_path):
    old_size_playerlog = 0
    pos_playerlog = 0
    old_size_chatlog = 0
    pos_chatlog = 0
    while True:
        runTimedEvents()
        # chatlog tailing
        new_size = os.stat(chat_log_path).st_size
        if new_size > old_size_chatlog:
            with open(chat_log_path, "r") as f:
                f.seek(pos_chatlog)
                for line in f:
                    print(line)
                    readLineChatLog(line)
                pos_chatlog = f.tell()
            old_size_chatlog = new_size

        # playerlog tailing
        new_size = os.stat(player_log_path).st_size
        if new_size > old_size_playerlog:
            with open(player_log_path, "r") as f:
                f.seek(pos_playerlog)
                for line in f:
                    print(line)
                    readLinePlayerLog(line)
                pos_playerlog = f.tell()
            old_size_playerlog = new_size

        time.sleep(1)


tail("Player.log", "./chatlogs/chatlog.txt")
