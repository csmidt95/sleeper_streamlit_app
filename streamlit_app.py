import streamlit as st
import pandas as pd
from sleeper_functions import get_all_league_for_user_info, get_users_in_leauge, get_rosters, get_all_matchups, get_user_id
import numpy as np
import duckdb
from duck_db_query_functions import create_base_table
import time
import requests
import random



@st.cache_resource
def create_duckdb_database(df1, df2, df3, df4):
    """
    Creates an in-memory DuckDB database and stores multiple DataFrames.
    This function is cached to avoid recreating the database on every app rerun.
    """
    tables_to_create = ['leagues', 'users', 'rosters', 'matchups']
    
    # Create an in-memory DuckDB database
    conn = duckdb.connect(database=':memory:')
        
    # Store DataFrames in the DuckDB database
    for table_name in tables_to_create:
        ex_statement = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM {table_name}"
        conn.execute(ex_statement)

    #create and cache the base table    
    create_base_table(conn, st.session_state.user_id_input)
    return conn

@st.cache_data
def getting_frisky_fantasy_facts(user_id, year, league_id):
    users = get_users_in_leauge(league_id)
    rosters = get_rosters(league_id)
    matchups = get_all_matchups(league_id)
    leagues = get_all_league_for_user_info(user_id, year)
    return users, rosters, matchups, leagues


year_options = pd.DataFrame({
    'years': [2023, 2024],
    })


# Initialize session state
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "user_id_input" not in st.session_state:
    st.session_state.user_id_input = ""

if "user_selected_year" not in st.session_state:
    st.session_state.user_selected_year = None

if "user_selected_league" not in st.session_state:
    st.session_state.user_selected_league = None

if "user_selected_league_id" not in st.session_state:
    st.session_state.user_selected_league_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "league_submitted" not in st.session_state:
    st.session_state.league_submitted = False

# Step 1: Take input from the user
st.title("Sleeper App Data Analytics")
#if not st.session_state.submitted:
    # Capture user input

#Get the user name
user_name = st.text_input(
    "What is your Sleeper User Name?", value=st.session_state.user_name
)

st.session_state.user_id_input = get_user_id(user_name)

st.session_state.user_selected_year = st.selectbox(
    'What year are you interested in?',
    year_options['years']
)

# On submit, update session state
if st.button("Submit"):
    st.session_state.submitted = True


if st.session_state.submitted:
    # Use stored values from session state
    user_id_input = st.session_state.user_id_input
    user_selected_year = st.session_state.user_selected_year

    # Creating the league pandas dataframe 
    leagues_for_user = get_all_league_for_user_info(user_id_input, user_selected_year)

    #Display league options
    league_selection = st.selectbox(
        'Which league do you want to learn more about?',
        leagues_for_user['League_Name']
    )

    # On submit, update session state
    if st.button("Submit", key = 'league_selection_button'):
        st.session_state.league_submitted = True
        st.session_state.user_selected_league = league_selection
        st.session_state.user_selected_league_id = leagues_for_user[leagues_for_user['League_Name'] == league_selection]['league_id'].iloc[0]

        # st.session_state.user_selected_league
        # st.session_state.user_selected_league_id


if st.session_state.league_submitted:
    users, rosters, matchups, leagues = getting_frisky_fantasy_facts(st.session_state.user_id_input, st.session_state.user_selected_year, st.session_state.user_selected_league_id)

    db_connection = create_duckdb_database(users, rosters, matchups, leagues)


    # Create two columns for buttons
    podium, luck = st.columns(2)

    # Button 1: Podium Scores
    with podium:
        if st.button("Click here to look into Podium Scores"):
            st.session_state.page = "podium"

    # Button 2: Luck Analyzer
    with luck:
        if st.button("Click here to look into the Luck Analyzer"):
            st.session_state.page = "luck"

    # Display content based on button click
    if "page" in st.session_state:
        if st.session_state.page == "podium":
            #create a line for organization
            st.markdown("<hr style='border:2px solid black'>", unsafe_allow_html=True)

            #set context for database query
            result_func = "select * from average_rank_table"
            df = db_connection.execute(result_func).df()
            df.rename(columns={'player_1': 'Player Name', 'avg_score_rank' : 'Avg Podium Position', 'avg_opponent_score_rank' : 'Avg Opponent Podium Position'}, inplace=True)
            df = df.reset_index(drop=True)

            #Best user
            best_user = df.loc[df["Avg Podium Position"].idxmin()]
            worst_user = df.loc[df["Avg Podium Position"].idxmax()]

            #hardest/easiest opponent
            hardest_opponent = df.loc[df["Avg Opponent Podium Position"].idxmin()]
            easiest_opponent = df.loc[df["Avg Opponent Podium Position"].idxmax()]


            #create columns
            col1, col2 = st.columns([2, 1])  # Adjust ratio as needed

            with col1:
                st.write("### Podium Score Table")
                st.dataframe(df, height=490, hide_index = True)

            with col2:
                st.write("### Podium Performance Summary")
                st.write(f"**{best_user['Player Name']}** had the best average podium position of **{best_user['Avg Podium Position']} place**.")
                st.write(f"**{worst_user['Player Name']}** had the worst average podium position of **{worst_user['Avg Podium Position']} place**.")
                st.markdown("<hr style='border:1px solid black'>", unsafe_allow_html=True)
                st.write(f"**{hardest_opponent['Player Name']}** played against the hardest schedule - their opponent's average podium position was **{hardest_opponent['Avg Opponent Podium Position']} place**.")
                st.write(f"**{easiest_opponent['Player Name']}** played against the easiest schedule - their opponent's average podium position was **{easiest_opponent['Avg Opponent Podium Position']} place**.")
            

        elif st.session_state.page == "luck":
            #create a line for organization
            st.markdown("<hr style='border:2px solid black'>", unsafe_allow_html=True)

            st.write("### Luck Analyzer")
            st.write("We have run analysis on who the Fantasy Gods blessed, and who the Fantasy Gods cursed...")
            #time.sleep(2)  # Adds a 2-second delay
            st.markdown("""
            ### To calculate luck scores, we looked at:
            - Close wins/losses
            - Instances where matchups were lucky/unlucky, i.e. the top scorer of the weel matched up against the 2nd top scorer
            """)

            #create columns
            col1, col2 = st.columns([1, 1])  # Adjust ratio as needed

            #set context for database query
            result_func = "select * from luck_score_agg"
            df = db_connection.execute(result_func).df()
            df.rename(columns={'player_1':'Player Name', 'total_luck_score':'Luck Score', 'luck_rank':'Luck Rank'}, inplace = True)

            #luckiest user
            luckiest_rank = df['Luck Rank'].min()
            luckiest_players = df[df['Luck Rank'] == luckiest_rank]['Player Name'].to_list()

            #unluckiest user
            unluckiest_rank = df['Luck Rank'].max()
            unluckiest_players = df[df['Luck Rank'] == unluckiest_rank]['Player Name'].to_list()


            # Your Giphy API Key
            GIPHY_API_KEY = "rr8NvesCqJ2x1dUxWNxFwlyUcM1DYlyS"
            theme = 'gambling victory'
            url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={theme}&limit=10&rating=g"
            response = requests.get(url).json()
            gif_url = random.choice(response["data"])["images"]["original"]["url"]


            with col1:
                st.dataframe(df, hide_index = True)
            
            with col2:
                # Dynamically format the sentence
                if len(luckiest_players) == 1:
                    sentence = f"Player **{luckiest_players[0]}** was the luckiest this year."
                elif len(luckiest_players) == 2:
                    sentence = f"Players **{luckiest_players[0]}** and **{luckiest_players[1]}** were the luckiest this year."
                else:
                    sentence = f"Players {', '.join(luckiest_players[:-1])} and {luckiest_players[-1]} were the luckiest this year."

                # Output the result
                st.write(sentence)
                st.image(gif_url, use_container_width=True)


                                # Dynamically format the sentence
                if len(unluckiest_players) == 1:
                    sentence = f"Player **{unluckiest_players[0]}** was the unluckiest this year."
                elif len(unluckiest_players) == 2:
                    sentence = f"Players **{unluckiest_players[0]}** and **{unluckiest_players[1]}** were the luckiest this year."
                else:
                    sentence = f"Players **{', '.join(unluckiest_players[:-1])}** and **{unluckiest_players[-1]}** were the luckiest this year."

                # Output the result
                st.write(sentence)
            
            all_matchup_query = f"""select 
                                        week_number,
                                        player_1,
                                        player_2,
                                        player_1_points,
                                        player_2_points,
                                        score_delta,
                                        matchup_delta_luck_event,
                                        matchup_delta_luck_score,
                                        player_1_score_rank,
                                        player_2_score_rank,
                                        podium_luck_event,
                                        podium_luck_score,
                                        luck_score as total_luck_score
                                    from weekly_matchup_ranks
                                 """
            df_all_matchups = db_connection.execute(all_matchup_query).df()

                #Display league options
            player_selection = st.selectbox(
                "Which player's lucky/unlucky games do you want to see?",
                df_all_matchups['player_1'].unique()
            )

            specific_user_query = f"""select 
                                        week_number,
                                        player_1,
                                        player_2,
                                        player_1_points,
                                        player_2_points,
                                        score_delta,
                                        matchup_delta_luck_event,
                                        matchup_delta_luck_score,
                                        player_1_score_rank,
                                        player_2_score_rank,
                                        podium_luck_event,
                                        podium_luck_score,
                                        luck_score as total_luck_score
                                    from weekly_matchup_ranks where player_1 = '{player_selection}' and luck_score <> 0
                                 """
            specific_user_luck_df = db_connection.execute(specific_user_query).df()
            st.dataframe(specific_user_luck_df, hide_index = True)




   

