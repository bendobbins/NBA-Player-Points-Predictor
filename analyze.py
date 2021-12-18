import numpy as np
from sklearn.linear_model import LinearRegression

def make_datapoints(dictionaryList, dependent, independent1, independent2, independent3):
    """
    Given a list of dictionaries full of stats, a dependent variable and 2 or 3 independent variables (all keys in each
    dictionary in the list), return a list of independent vars from each dictionary and another of dependent vars from each dictionary.

    dictionaryList -- List of dictionaries
    dependent -- String and key in each dictionary
    independent1, 2 & 3 -- Strings and keys in each dictionary
    """
    x = []
    y = []
    for dictionary in dictionaryList:
        if dictionary:      # If player has stats for that game
            if independent3:        # If 3 independent vars
                x.append([dictionary[independent1], dictionary[independent2], dictionary[independent3]])
                y.append(dictionary[dependent])
            else:
                x.append([dictionary[independent1], dictionary[independent2]])
                y.append(dictionary[dependent])

    return (x, y)


def linear_regression(x, y):
    """
    Given two sets of data points where the x set is multi-dimensional, create a multiple linear regression model and
    return the coefficients as well as the intercept for the model.
    """
    x, y = np.array(x), np.array(y)     # Convert to np array for sklearn module
    model = LinearRegression().fit(x, y)
    coefs = list(model.coef_)
    intercept = model.intercept_
    return [coefs, intercept]


def minutes_estimation(stats):
    """
    Given a list of dictionaries where each dictionary contains stats from one game for one player, determine how many
    games a player missed based on how many dictionaries are replaced with None. Create a prediction on how many minutes
    the player will play in their next game based on their recent minutes played. Return prediction and boolean dic for tracking games missed.
    """
    limitations = {
        "lastGame": False,
        "last5": False,
        "15": False,
        "10last15": False
    }

    gamesMissed = 0
    for i in range(len(stats)):
        if gamesMissed == 1 and i == 1:     # If player missed last game
            limitations["lastGame"] = True
        if gamesMissed == 5 and i == 5:       # If player missed last five games
            limitations["last5"] = True
        if gamesMissed >= 10 and i == 15:        # If player missed 10 of last 15 games
            limitations["10last15"] = True
        if gamesMissed == 15:       # If the player missed 15 games
            limitations["15"] = True
        if not stats[i]:
            gamesMissed += 1
    if gamesMissed == len(stats):       # If player missed all games
        return limitations, None
    
    predictedMinutes = 0.0
    if limitations["last5"] or limitations["10last15"]:     # If player missed a lot of recent games, use all data to estimate minutes
        for game in stats:
            if game:
                predictedMinutes += game["mins"]
        predictedMinutes /= len(stats) - gamesMissed

    else:                                         # If player did not miss a lof of recent games, use more recent samples and less data
        counter = 0                               # Idea being more recent games give more accurate estimate of mins played
        missed = 0
        for i in range(len(stats)) if len(stats) < 15 else range(15):
            if stats[i]:
                predictedMinutes += stats[i]["mins"]
            else:
                missed += 1
            counter += 1
        predictedMinutes /= counter - missed

    return limitations, round(predictedMinutes)


def prediction(minutes, models, ratings):
    """
    Given a player's predicted minutes played, a dictionary of statistical models for each key (corresponding to a stat) and the 
    next opposing team's ratings, return a dictionary of predictions for what stats a player will have in their next game.
    """
    predictedStats = {}
    # Each key corresponds to a list of values that multiply with corresponding coefficients in the models dict to achieve predictions
    plugIns = {
        "rb": [minutes, ratings[2]],
        "ast": [minutes, ratings[2], ratings[1]],
        "stl": [minutes, ratings[2], ratings[0]],
        "blk": [minutes, ratings[2], ratings[0]],
        "tov": [minutes, ratings[2], ratings[1]],
        "fta": [minutes, ratings[2], ratings[1]],
        "3pa": [minutes, ratings[2], ratings[1]],
        "fga": [minutes, ratings[2], ratings[1]],
    }

    for key in plugIns:
        predictedStats[key] = models[key][1]        # Set initial value of prediction equal to value of intercept for current stat
        for i in range(len(models[key][0])):        # For each coefficient
            predictedStats[key] += models[key][0][i] * plugIns[key][i]      # Add coefficient multiplied by corresponding value (minutes or some rating)
        predictedStats[key] = round(predictedStats[key])

    # Plugins that could not be defined in the first dict because they rely on results from the first for loop
    dependentPlugIns = {
        "fgm": [predictedStats["fga"], ratings[2], ratings[1]],
        "3pm": [predictedStats["3pa"], ratings[2], ratings[1]],
        "ftm": [predictedStats["fta"], ratings[2]]
    }
    for key in dependentPlugIns:
        predictedStats[key] = models[key][1]        # Same process as above
        for i in range(len(models[key][0])):
            predictedStats[key] += models[key][0][i] * dependentPlugIns[key][i]
        predictedStats[key] = round(predictedStats[key])
    
    predictedStats["mins"] = minutes
    predictedStats["rtgs"] = ratings
    
    return predictedStats