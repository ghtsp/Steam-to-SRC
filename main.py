import requests
import csv
import time
import re

SteamKey = "Input a steam key"
SteamID = "Input a steam ID"

SteamQuery = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + SteamKey + "&steamid=" \
             + SteamID + "&format=json&include_appinfo=1"

# Get a list of games in the user's steam library
SteamResponse = requests.get(SteamQuery)
SteamJSON = SteamResponse.json()
GameCount = SteamJSON["response"]["game_count"]

# Set count to 10 for easier debugging of this script
# GameCount = 10

# initialize some stuff
GamesList = [0] * GameCount
MissingGames = []
ILBoards = []
ErrorBoards = []
AppidList = [0] * GameCount
CurrentAppid = 0
RunCountsList = [0] * GameCount

# For each game, look for an SRC page and collect desired info
for x in range(GameCount):
    time.sleep(0.7)
    CurrentAppid = 0
    # Store each game's title in a list
    CurrentGame = SteamJSON["response"]["games"][x]['name']
    print(CurrentGame)
    GamesList[x] = CurrentGame

    # For each game, use the SRC API to search for a corresponding leaderboard and store the appid
    SRCSearchQuery = "https://www.speedrun.com/api/v1/games?name=" + CurrentGame
    SRCSearchResponse = requests.get(SRCSearchQuery)
    SRCSearchJSON = SRCSearchResponse.json()
    print(SRCSearchJSON)
    SRCSearchData = SRCSearchJSON["data"]
    if SRCSearchData:
        CurrentAppid = SRCSearchData[0]["id"]
        AppidList[x] = CurrentAppid
    else:
        # For any games not found, try an alternate search method
        # Try without special characters, extra spaces, tabs, etc
        CurrentGameNoSpecials = re.sub(r"[^a-zA-Z0-9 ]", "", CurrentGame)
        CurrentGameNoSpecials = ' '.join(CurrentGameNoSpecials.split())
        print(CurrentGameNoSpecials)
        SRCSearchQueryNoSpecials = "https://www.speedrun.com/api/v1/games?name=" + CurrentGameNoSpecials
        SRCSearchResponseNoSpecials = requests.get(SRCSearchQueryNoSpecials)
        SRCSearchJSONNoSpecials = SRCSearchResponseNoSpecials.json()
        SRCSearchDataNoSpecials = SRCSearchJSONNoSpecials["data"]
        if SRCSearchDataNoSpecials:
            CurrentAppid = SRCSearchDataNoSpecials[0]["id"]
            AppidList[x] = CurrentAppid
            print("found one using no specials")
            print(CurrentGameNoSpecials)
        else:
            # For any games still not found, try another alternate search method
            # Try to remove 'edition' labels
            EditionCheck = CurrentGameNoSpecials[-7:]
            GOTYCheck = CurrentGameNoSpecials[-24:]
            CurrentGameNoEdition = CurrentGameNoSpecials
            # remove Game of the Year Edition labels
            if GOTYCheck == "Game of the Year Edition":
                CurrentGameNoEdition = CurrentGameNoSpecials.rsplit(' ', 5)[0]
            else:
                # Remove any 2 word edition labels
                if EditionCheck == "Edition":
                    CurrentGameNoEdition = CurrentGameNoSpecials.rsplit(' ', 2)[0]
            # TODO: Try to find a way to remove edition labels longer than 2 words
            SRCSearchQueryNoEdition = "https://www.speedrun.com/api/v1/games?name=" + CurrentGameNoEdition
            SRCSearchResponseNoEdition = requests.get(SRCSearchQueryNoEdition)
            SRCSearchJSONNoEdition = SRCSearchResponseNoEdition.json()
            SRCSearchDataNoEdition = SRCSearchJSONNoEdition["data"]
            if SRCSearchDataNoEdition:
                CurrentAppid = SRCSearchDataNoEdition[0]["id"]
                AppidList[x] = CurrentAppid
                print(SRCSearchDataNoEdition)
                print("found one using no edition")
                print(CurrentGameNoEdition)
            else:
                # For any games still not found, try another search method
                # TODO: add more search methods
                NoError = 1
    # TODO: Add error checking for incorrect matches, such as matching the first game in the list of all SRC games
    # Use the SRC API to calculate the desired outputs (ie number of runs in main category)
    if CurrentAppid != 0:
        SRCGameQuery = "https://www.speedrun.com/api/v1/games/" + CurrentAppid
        SRCGameResponse = requests.get(SRCGameQuery)
        SRCGameJSON = SRCGameResponse.json()
        links = SRCGameJSON['data']['links']
        index = len(links)
        Catid = links[index-1]['uri'][-8:]
        if Catid == "ed-games":
            # If the board defaults to an IL board, add the index to a list
            ILBoards.append(x)
        else:
            SRCLeaderboardQuery = "https://www.speedrun.com/api/v1/leaderboards/" + CurrentAppid + "/category/" + Catid
            SRCLeaderboardResponse = requests.get(SRCLeaderboardQuery)
            SRCLeaderboardJSON = SRCLeaderboardResponse.json()
            LevelCheck = list(SRCLeaderboardJSON.values())[0]
            if LevelCheck == 400:
                # If the default category needs a level despite not being an IL board, add the index to a list
                ErrorBoards.append(x)
            else:
                RunList = SRCLeaderboardJSON['data']["runs"]
                RunCount = len(RunList)
                RunCountsList[x] = RunCount

# TODO: Do something with IL boards
# TODO: Do something with error boards

# Output the results in a user-friendly format

rows = zip(GamesList, RunCountsList)
with open('Steam_SRC.csv','w',newline='') as csvfile:
    LineWriter = csv.writer(csvfile, delimiter='|', quotechar='_')
    LineWriter.writerows(rows)
print(GamesList)
print(RunCountsList)

