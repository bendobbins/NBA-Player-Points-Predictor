from bs4 import BeautifulSoup as bs
import requests
from datetime import datetime as dt

from analyze import make_datapoints, linear_regression, minutes_estimation, prediction

SITE = "https://www.basketball-reference.com"

if int(dt.now().strftime('%m')) > 8 and int(dt.now().strftime('%m')) <= 12:
    YEAR = int(dt.now().strftime('%Y')) + 1
else:
    YEAR = int(dt.now().strftime('%Y'))

TEAMS = {
    "ATL": "Atlanta Hawks",
    "BRK": "Brooklyn Nets",
    "BOS": "Boston Celtics",
    "CHA": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHO": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"
}


def player_link(player):
    """
    Given the name of an NBA player, the function returns the html of their gamelogs on basketball reference for the current year.
    If player is not in the NBA, function returns None.
    """
    if not player:
        return None
    names = player.lower().split()      # List of lowercase first and last name
    if len(names) == 1:
        return None
    count = 1

    while True:
        # Construct proper URL for request
        request = requests.get(SITE + "/players/" + names[1][0] + '/' + names[1][:5] + names[0][:2] + '0' + str(count) + '/gamelog/' + str(YEAR)).text
        playerHTML = bs(request, 'lxml')
        header = playerHTML.find('h1').text.lower().split()     # Split the first header into a list of lowercase strings

        if header[1] != names[1]:       # If the page is not for an NBA player, the header will not include their last name
            return None
        if header[0] == names[0]:       # Return page if first name matches first name of player being searched
            return request
        count += 1      # Basketball reference deals with players with the same last name and same first 2 letters of first name by
                        # numbering them in the URL, so this is to check all those players. Once numbers run out, page will redirect to non-player page


def team_schedule_link(team):
    """
    Given the three letter abbreviation for a basketball team, return html of their schedule page for the current year on basketball reference.
    """
    return requests.get(SITE + "/teams/" + team + '/' + str(YEAR) + "_games.html").text
        

def next_opposing_team(source):
    """
    Given the html for a team schedule, return the link w/out domain for the basketball reference page of their next opponent. Return None if no valid games.
    """
    upcomingGames = bs(source, 'lxml')
    table = upcomingGames.find('tbody')
    rows = table.find_all('tr')

    link = ''
    for row in rows:
        data = row.find_all('td')       # Check all data in schedule table
        if data:
            if not data[6].text:        # This is the W/L category, which is left blank if a game has not been played
                link = data[5].a.get('href')        # Opposing team link
                team = data[5].a.text
                break
    
    if not link:
        return None, None

    return link, team


def get_opposing_ratings(link):
    """
    Given the link w/out domain to a team website, return a list of the offensive, defensive and pace ratings for that team.
    """
    oppTeamSite = SITE + link
    oppHTML = bs(requests.get(oppTeamSite).text, 'lxml')
    paragraphs = oppHTML.find_all('p')

    for paragraph in paragraphs:
        if paragraph.a:
            if paragraph.a.text == "SRS":
                paceText = paragraph.text.split('\n')
            if paragraph.a.text == "Off Rtg":       # Find the ratings, split them into a list
                ratingsText = paragraph.text.split('\n')
    
    if not ratingsText or not paceText:
        return None

    ratingsTextCleaned = clean_ratings(ratingsText)     # Ratings are not well formatted, so clean up empty strings and whitespace
    paceTextCleaned = clean_ratings(paceText)
    paceTextCleaned.pop(0)      # Get rid of SRS, not important
    ratingsTextCleaned.pop(2)       # Get rid of net rating, not important
    cleanedText = ratingsTextCleaned + paceTextCleaned

    ratings = []
    for rating in cleanedText:
        paren = rating.index('(')
        try:
            ratings.append(int(rating[paren + 1:paren + 3]))      # Get number rating for offense and defense
        except ValueError:
            ratings.append(int(rating[paren + 1]))

    return ratings


def clean_ratings(ratings):
    """
    Given a list of strings, remove whitespace and return a list of all non-empty strings.
    """
    cleaned = []
    for rating in ratings:
        rating = rating.strip()
        if rating:
            cleaned.append(rating)
    return cleaned


def get_games(source):
    """
    Given the html for a player's gamelog, return their stats for the past season, as well as the 3 letter abbrev for their current team.
    """
    playerHTML = bs(source, 'lxml')
    table = playerHTML.find('tbody')
    if not table:
        return None, None
    rows = table.find_all('tr')

    games = []
    team = ""
    for row in rows:
        data = row.find_all('td')       # Get data from every column of row
        stats = []
        counter = 0
        for tag in data:
            try:
                stat = float(tag.text)      # Turn numeric values into floats, append all to stats
            except ValueError:
                stat = tag.text
            stats.append(stat)
            if counter == 5:        # Link to opposing team always listed in 6th data column
                oppTeamLink = tag.a.get('href')
            counter += 1

        if stats:
            for i in range(7):      # Get rid of useless info
                if i == 3:
                    team = stats.pop(0)     # Get team of player
                else:
                    stats.pop(0)
            if len(stats) != 1:
                stats = clean_stats(stats)      # Make list of only needed values
                ratings = get_opposing_ratings(oppTeamLink) 
                stats += ratings        # Add opponent offensive, defensive and pace ratings to list
            games.append(stats)

    games.reverse()     # Reverse so that most recent games are at the start
    return games, team
    

def clean_stats(stats):
    """
    Given a list of stats for one player in one game, remove all unneeded values from list and convert minutes played to an integer.
    """
    stats.pop(0)

    # Convert time to int
    time = stats.pop(0).split(":")
    if int(time[1]) > 30:
        approxMins = int(time[0]) + 1
    else:
        approxMins = int(time[0])
    
    # Remove unneeded values
    stats.pop(-2)
    for _ in range(3):
        stats.pop(-1)
    for _ in range(2):
        stats.pop(9)
    for i in range(1, 4):
        stats.pop(i * 2)
    stats.append(approxMins)

    return stats


def organize_stats(stats):
    """
    Given a list of lists, where each list is stats from a separate game for one player, return a list of dictionaries mapping each stat
    to its key for easier accessibility. Only use the most recent 30 games.
    """
    gameDics = []
    for i in range(len(stats)) if len(stats) < 31 else range(30):       # Most recent games
        if len(stats[i]) == 1:
            gameDics.append(None)       # If player was inactive or did not play
        else:
            gameDic = {}
            keys = ["fgm", "fga", "3pm", "3pa", "ftm", "fta", "rb", "ast", "stl", "blk", "tov", "mins", "oppOff", "oppDef", "oppPace"]
            for j in range(len(keys)):
                gameDic[keys[j]] = stats[i][j]      # Map stats to keys
            gameDics.append(gameDic)

    return gameDics


def make_regression_dictionary(orgStats):
    """
    Given a list of dictionaries where each dictionary has stats for one player from one game, define the variables that
    will be used to create models for each stat, then create models for each stat, and return dictionary of models where
    each stat is the key for its own model.
    """
    # Define what variables will be used to create a model for dependent variables (keys)
    comparisons = {
        "rb": ["mins", "oppPace"],
        "ast": ["mins", "oppPace", "oppDef"],
        "stl": ["mins", "oppPace", "oppOff"],
        "blk": ["mins", "oppPace", "oppOff"],
        "tov": ["mins", "oppPace", "oppDef"],
        "fta": ["mins", "oppPace", "oppDef"],
        "3pa": ["mins", "oppPace", "oppDef"],
        "fga": ["mins", "oppPace", "oppDef"],
        "fgm": ["fga", "oppPace", "oppDef"],
        "3pm": ["3pa", "oppPace", "oppDef"],
        "ftm": ["fta", "oppPace"]
    }
    regressions = {}

    for comparison in comparisons:
        # Create models by getting datapoints for each variable, then using multiple linear regression
        if len(comparisons[comparison]) == 3:
            regressions[comparison] = linear_regression(*make_datapoints(orgStats, comparison, *comparisons[comparison]))
        else:
            regressions[comparison] = linear_regression(*make_datapoints(orgStats, comparison, *comparisons[comparison], None))
        
    return regressions


def format_stats(warnings, stats):
    """
    Given a dictionary with info about a players missed games and a dictionary with their predicted stats for the next game, form the message to be displayed
    for the user in the GUI. Return the message as a string.
    """
    # Add warning messages if player has missed certain amount of games
    message = ""
    if warnings['last5']:
        message += f"{stats['plyr']} has missed his last 5 games, so he might be injured (or he sucks :P). Either way, the prediction might be less accurate with less recent data.\n\n"
    elif warnings['10last15']:
        message += f"{stats['plyr']} has missed 10 of their last 15 games, so the prediction might be less accurate with less recent data.\n\n"
    elif warnings['15']:
        message += f"{stats['plyr']} has missed 15 of their last 30 games (or however many have been played so far), so the prediction might be less accurate with less data.\n\n"
    elif warnings['lastGame']:
        message += f"{stats['plyr']} missed their last game, so they might not play the next one. Regardless, here is the prediction: \n"
    
    # Formulate message from predicted stats
    points = ((stats['fgm'] - stats['3pm']) * 2) + (stats['3pm'] * 3) + stats['ftm']
    message += f"{stats['plyr']} of the {stats['team']} is projected to play {stats['mins']} minutes against the {stats['oppTeam']}"
    message += f", who have current offensive, defensive and pace ratings of {stats['rtgs'][0]}, {stats['rtgs'][1]} and {stats['rtgs'][2]} respectively."
    message += f" Based on these values and past stats for {stats['plyr']}, his predicted stats for the upcoming game are: \n"
    message += f"{points} pts, {stats['rb']} rbs, {stats['ast']} asts, {stats['stl']} stls, {stats['blk']} blks, {stats['tov']} tovs"
    message += f" on {stats['fgm']}/{stats['fga']} fgs, {stats['3pm']}/{stats['3pa']} 3ps and {stats['ftm']}/{stats['fta']} fts."
    return message


def make_message(player):
    """
    Given the name of an NBA player, return a string predicting the player's stats for their next game. Return some error message if something goes wrong.
    """
    playerLink = player_link(player)        # Get link to player page on basketball reference

    # If player named is not/never was in NBA
    if playerLink is None:
        return "Please enter the name of a valid NBA player"
    
    stats, playerTeam = get_games(playerLink)       # Get player stats, team

    # If player is retired
    if stats is None:
        return "Please enter the name of a current NBA player"

    # If no stats can be found for some reason (maybe very beginning of season)
    if not stats:
        return f"Could not find any stats from previous games this year for {player}"

    oppLink, oppTeam = next_opposing_team(team_schedule_link(playerTeam))       # Get opposing team site link and name

    # No upcoming games (maybe end/beginning of season)
    if oppLink is None:
        return f"Cannot find an upcoming game for {player}"

    oppRatings = get_opposing_ratings(oppLink)      # Get ratings for opposing team

    # If ratings can't be scraped from opposing team website (maybe due to website format change)
    if oppRatings is None:
        return f"Could not get ratings for {oppTeam}"
    
    orgStats = organize_stats(stats)        # Organize stats into dictionaries
    missedBools, minutes = minutes_estimation(orgStats)     # Estimate minutes player will play

    # If player has not played any games that are counted
    if minutes is None:
        return f"{player} has missed his last 30 games (or however many have been played so far). Hence, stats cannot be predicted."
    
    models = make_regression_dictionary(orgStats)       # Make statistical models to predict each stat
    stats = prediction(minutes, models, oppRatings)     # Predict stats
    stats["plyr"] = player
    stats["team"] = TEAMS[playerTeam]
    stats["oppTeam"] = oppTeam
    return format_stats(missedBools, stats)     # Return formatted string with predictions