import requests
import json
import pandas as pd

def get_all_league_for_user_info(user_id, season):
    #empty dict, going to add the data here
    result = {}
    
    #API request to get all of the leagues the user is in the selected season
    get_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
    r = requests.get(url= get_url)
    response_dict = json.loads(r.text)
    
    #Iterate through all the leagues for the user that season
    for i in range(len(response_dict)):
        result.update({response_dict[i]['league_id'] : { "League_Name": response_dict[i]['name'], 
                                                         "League_Year" : season, 
                                                         'User_ID' : user_id,
                                                         'League_size' : response_dict[i]['settings']['num_teams'],
                                                         'Number_of_Playoff_Teams' : response_dict[i]['settings']['playoff_teams'],
                                                         'Playoffs_Start_Week' : response_dict[i]['settings']['playoff_week_start']
                      }})
    df = pd.DataFrame.from_dict(result, orient='index').reset_index()
    df = df.rename(columns={'index': 'league_id'})
    return df

def get_users_in_leauge(league_id):
    get_url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    r = requests.get(url= get_url)
    response_dict = json.loads(r.text)
    df = pd.DataFrame(response_dict)
    return df[['user_id', 'display_name', 'league_id']]

def get_rosters(league_id):
    get_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    r = requests.get(url= get_url)
    response_dict = json.loads(r.text)
    columns_to_keep = ['roster_id', 'league_id', 'metadata', 'owner_id', 'settings']
    df = pd.DataFrame(response_dict)[columns_to_keep]

    #I want to keep the same naming convention where possible, owner_id = user_id
    df = df.rename(columns={"owner_id": "user_id"})
    return df

#Let's start with assuming 18 weeks
def get_all_matchups(league_id):
    df = pd.DataFrame()
    for i in range(1, 19):
        get_url = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{i}"
        r = requests.get(url= get_url)
        response_dict = json.loads(r.text)
        new_data = pd.DataFrame(response_dict)
        new_data['Week_Number'] = i
        df = pd.concat([df, new_data], ignore_index=True)
    df['league_id'] = league_id
    return df