
def create_base_table(conn, user_id):
    query = """
        create or replace table weekly_matchup_ranks as (
            with data as (
                select
                    u.display_name,
                    u.user_id,
                    m.*,
                    rank() over (partition by Week_Number order by points desc) as score_rank
                from matchups as m
                left join rosters as r
                    on m.roster_id = r.roster_id
                left join users as u
                    on r.user_id = u.user_id
                order by u.display_name, m.Week_Number
            )

            select
                d1.user_id as player_1_user,
                d1.display_name as player_1,
                d1.points as player_1_points,
                d1.score_rank as player_1_score_rank,
                d2.display_name as player_2,
                d2.points as player_2_points,
                d2.score_rank as player_2_score_rank,
                d1.Week_Number,
                player_1_points > player_2_points as player_1_win,
                abs(player_1_points - player_2_points) as score_delta,

                --Podium Luck
                case
                    when player_1_win and player_1_score_rank = 11 then 'Super Lucky'
                    when player_1_win and player_1_score_rank = 10 then 'Very Lucky'
                    when player_1_win and player_1_score_rank > 6 then 'Lucky'
                    when not player_1_win and player_1_score_rank = 2 then 'Super Unlucky'
                    when not player_1_win and player_1_score_rank = 3 then 'Very Unlucky'
                    when not player_1_win and player_1_score_rank <= 6 then 'Unlucky'
                    else 'Neutral'
                end as podium_luck_event,

                case podium_luck_event
                    when 'Super Lucky' then 4
                    when 'Very Lucky' then 2
                    when 'Lucky' then 1
                    when 'Super Unlucky' then -4
                    when 'Very Unlucky' then -2
                    when 'Unlucky' then -1
                    else 0
                end as podium_luck_score,

                --Score delta Luck
                case
                    when player_1_win and score_delta < 1 then 'Super Lucky'
                    when player_1_win and score_delta < 2 then 'Very Lucky'
                    when player_1_win and score_delta < 3 then 'Lucky'
                    when not player_1_win and score_delta < 1 then 'Super Unlucky'
                    when not player_1_win and score_delta < 2 then 'Very Unlucky'
                    when not player_1_win and score_delta < 3 then 'Unlucky'
                    else 'Neutral'
                end as matchup_delta_luck_event,

                case matchup_delta_luck_event
                    when 'Super Lucky' then 4
                    when 'Very Lucky' then 2
                    when 'Lucky' then 1
                    when 'Super Unlucky' then -4
                    when 'Very Unlucky' then -2
                    when 'Unlucky' then -1
                    else 0
                end as matchup_delta_luck_score,

                matchup_delta_luck_score + podium_luck_score  as luck_score
            from data as d1
            inner join data as d2
                on d1.matchup_id = d2.matchup_id
                and d1.Week_Number = d2.Week_Number
                and d1.roster_id <> d2.roster_id
            order by d1.display_name, d1.Week_Number
            );
        """
    conn.execute(query)

    plot_data_query = f"""
                create or replace table user_rank_plot as (
                    select
                            week_number,
                            player_1_score_rank,
                            player_2_score_rank
                    from weekly_matchup_ranks
                    where player_1_user = {user_id}
                    order by week_number
                )
                """
    conn.execute(plot_data_query)

    average_rank_query = """
                create or replace table average_rank_table as (
                    select
                        player_1,
                        round(avg(player_1_score_rank), 1) as avg_score_rank,
                        round(avg(player_2_score_rank), 1) as avg_opponent_score_rank
                    from weekly_matchup_ranks
                    group by 1
                    order by avg_score_rank
                )
                """

    conn.execute(average_rank_query)

    luck_score_agg_query = """
                         create or replace table luck_score_agg as (
                            select player_1,
                                sum(luck_score) as total_luck_score,
                                rank() over (order by total_luck_score desc) as luck_rank

                            from weekly_matchup_ranks
                            group by 1
                            order by luck_rank
                            )
                            """
    conn.execute(luck_score_agg_query)

