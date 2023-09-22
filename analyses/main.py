import copy
import datetime as dt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler


def read_data():
    luth_data = pd.read_excel("../nba harris brand platform cities.xlsx", sheet_name=[3, 4, 6, 7, 8, 9, 10], index_col=0, header=1)
    nba_team_performance = pd.read_excel("../nba harris brand platform cities.xlsx", sheet_name=[7], index_col=0, header=32, nrows=30)
    #nba_team_performance_po = pd.read_excel("../nba harris brand platform cities.xlsx", sheet_name=[1], index_col=0, header=1, usecols='I:L')
    nba_hbp = pd.read_excel("../nba harris brand platform cities.xlsx", sheet_name=[2], index_col=0, header=0)
    return luth_data[3], luth_data[4], luth_data[6], nba_hbp[2], nba_team_performance[7], luth_data[8], luth_data[9], luth_data[10]


def get_month_of_season(month):
    if month.month == 7 or month.month == 8 or month.month == 9:
        return 0
    elif month.month >= 10:
        return month.month - 9
    else:
        return month.month + 3


def get_part_of_season(month):
    if month.month == 4 or month.month == 5 or month.month == 6:
        return "Playoffs"
    elif month.month >= 10:
        return "First Half"
    elif month.month <= 3:
        return "Second Half"
    else:
        return "Offseason"


def get_team_level(team):
    if team in ["Phoenix Suns", "Memphis Grizzlies", "Boston Celtics", "Milwaukee Bucks", "Philadelphia 76ers", "Utah Jazz", "Denver Nuggets"]:
        return "Top Third"
    elif team in ["Chicago Bulls", "Minnesota Timberwolves", "Cleveland Cavaliers", "Atlanta Hawks", "Charlotte Hornets"]:
        return "Middle Third"
    elif team in ["New Orleans Pelicans", "Washington Wizards", "Portland Trail Blazers", "Oklahoma City Thunder", "Detroit Pistons"]:
        return "Bottom Third"
    elif team == "No Team":
        return "No Team"
    else:
        return "N/A"


def process_data(luth_users, luth, samba, hbp, nba_team_perf, samba_total_users, luth_total_users, luth_part_of_season):
    print()
    hbp = hbp.drop(hbp.columns[8:], axis=1)
    # make N/As in hbp team names into strings
    # make N/As in luth and samba team names into strings
    luth = luth.replace(np.nan, 'N/A', regex=True)
    luth_users = luth_users.replace(np.nan, 'N/A', regex=True)
    luth_part_of_season = luth_part_of_season.replace(np.nan, 'N/A', regex=True)
    # convert luth months to datetime months
    luth['Month'] = pd.to_datetime(luth['Month'], format='%Y%m')
    luth_users['Month'] = pd.to_datetime(luth_users['Month'], format='%Y%m')

    samba = samba.replace(np.nan, 'N/A', regex=True)
    hbp['NBA_team'] = hbp['NBA_team'].replace(np.nan, 'N/A', regex=True)
    # group hbp data by team, month
    hbp['Q1010_adj'] = hbp['Q1010'].apply(lambda x: 1 if x == 4 else np.nan if np.isnan(x) else 0)
    hbp['Q3010_adj'] = hbp['Q3010'].apply(lambda x: 1 if x == 3 else np.nan if np.isnan(x) else 0)
    hbp['Q1030_adj'] = hbp['Q1030'].apply(lambda x: 1 if x == 9 or x == 10 else np.nan if np.isnan(x) else 0)
    hbp['Q1040_adj'] = hbp['Q1040'].apply(lambda x: 1 if x == 1 else np.nan if np.isnan(x) else 0)
    hbp['Q1010_weighted'] = hbp['Q1010_adj'] * hbp['weightvalue']
    hbp['Q3010_weighted'] = hbp['Q3010_adj'] * hbp['weightvalue']
    hbp['Q1030_weighted'] = hbp['Q1030_adj'] * hbp['weightvalue']
    hbp['Q1040_weighted'] = hbp['Q1040_adj'] * hbp['weightvalue']
    # split nba team perf data into reg season and playoffs, stack nba team perf data so cols are team, month, win%, num of wins
    nba_team_perf_rs = nba_team_perf.iloc[:,:28].reset_index()
    nba_team_perf_po = nba_team_perf.iloc[:,28:].reset_index()
    nba_team_perf_rs = pd.wide_to_long(nba_team_perf_rs, ['win %', 'games won', 'cum. win %', 'cum. games won'], i='index', j='Month', sep=' ', suffix=r'[\d]{4}/[\d]{2}/[\d]{2}')
    nba_team_perf_po = pd.wide_to_long(nba_team_perf_po, ['playoff games'], i='index', j='Month', sep=' ', suffix=r'[\d]{4}/[\d]{2}/[\d]{2}')
    nba_team_perf_rs = nba_team_perf_rs.reset_index().rename(columns={"index": "Team"})
    nba_team_perf_po = nba_team_perf_po.reset_index().rename(columns={"index": "Team"})
    nba_team_perf_rs['Month'] = pd.to_datetime(nba_team_perf_rs['Month'], format='%Y/%m/%d')
    nba_team_perf_po['Month'] = pd.to_datetime(nba_team_perf_po['Month'], format='%Y/%m/%d')

    # join samba total user data to samba data
    samba_total_users = samba_total_users.reset_index()
    samba = samba.reset_index().join(samba_total_users.set_index(['dma', 'month']), on=['dma', 'Month'])
    samba = samba.set_index(['dma'])
    samba['weighted_num_users'] = samba['num_users'] * samba['weight avg (scaled hh weight)']
    samba = samba.drop(columns=['weight avg (scaled hh weight)'])

    # join luth total user data to luth data
    luth_total_users = luth_total_users.reset_index()
    luth = luth.reset_index().join(luth_total_users.set_index(['state', 'month']), on=['State', 'Month'])
    luth = luth.set_index(['State'])
    #luth_part_of_season = luth_part_of_season.reset_index().join(luth_total_users.set_index(['state', 'month']), on=['State', 'Month'])
    #luth_part_of_season = luth_part_of_season.set_index(['State'])

    # add month_of_season column - offseason=0
    nba_team_perf_rs['month_of_season'] = nba_team_perf_rs['Month'].apply(get_month_of_season)
    nba_team_perf_po['month_of_season'] = nba_team_perf_po['Month'].apply(get_month_of_season)
    nba_team_perf_rs['games played'] = nba_team_perf_rs['games won'] / nba_team_perf_rs['win %']

    # add part_of_season column to luth data
    luth['Part of Season'] = luth['Month'].apply(get_part_of_season)

    # drop N/A team (responses from area w/o NBA team)
    samba = samba[samba['team'] != 'N/A']
    return luth_users, luth, samba, hbp, nba_team_perf_rs, nba_team_perf_po, luth_part_of_season


def run_regression(samba, hbp, nba_team_perf_rs, nba_team_perf_po, luth_users):
    samba_by_team = samba.groupby(['team', 'Month']).sum().reset_index()
    # add shows/games watched per user columns
    samba_by_team['shows per user'] = samba_by_team['nba tv shows watched'] / samba_by_team['weighted_num_users']
    samba_by_team['games per user'] = samba_by_team['nba games watched'] / samba_by_team['weighted_num_users']
    samba_by_team['% users watched show'] = samba_by_team['nba tv shows watched - unique users'] / samba_by_team['weighted_num_users']
    samba_by_team['% users watched game'] = samba_by_team['nba games watched - unique users'] / samba_by_team['weighted_num_users']
    samba_by_team['month_of_yr'] = samba_by_team['Month'].dt.month

    # join data - rs
    rs_reg_data = nba_team_perf_rs.join(samba_by_team.set_index(['team', 'Month']), on=['Team', 'Month'])
    rs_reg_data = rs_reg_data.set_index('Team').drop(index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
                                          'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    # linear regression
    reg = LinearRegression()
    reg.fit(rs_reg_data[['games won']], rs_reg_data[['nba games watched']])
    reg1 = LinearRegression()
    reg1.fit(rs_reg_data[['games won', 'win %', 'cum. games won', 'cum. win %']], rs_reg_data[['games per user']])
    # statsmodel linear regression
    reg1_sm = sm.OLS(rs_reg_data[['games per user']], sm.add_constant(rs_reg_data[['games won', 'win %', 'month_of_season', 'cum. games won', 'cum. win %']])).fit()
    reg1_pred = reg1_sm.predict(sm.add_constant(rs_reg_data[['games won', 'win %', 'month_of_season', 'cum. games won', 'cum. win %']]))
    print(reg1_sm.summary())

    # same for playoffs
    # join data - po
    po_reg_data = nba_team_perf_po.join(samba_by_team.set_index(['team', 'Month']), on=['Team', 'Month'])
    po_reg_data = po_reg_data.set_index('Team').drop(
        index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
               'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    # linear regression
    reg_po = LinearRegression()
    reg_po.fit(po_reg_data[['playoff games']], po_reg_data[['games per user']])
    reg_po_sm = sm.OLS(po_reg_data[['games per user']], sm.add_constant(po_reg_data[['playoff games', 'month_of_season']])).fit()
    reg_po_pred = reg_po_sm.predict(sm.add_constant(po_reg_data[['playoff games', 'month_of_season']]))
    print(reg_po_sm.summary())



    hbp['month'] = hbp['date'].dt.to_period('M')
    hbp['month'] = hbp['month'].dt.to_timestamp()
    hbp['nearest_month'] = hbp['date'].apply(round_to_nearest_month)
    # add n size in groupby
    hbp_by_team = hbp.groupby(['NBA_team', 'month']).agg(n=('Q1010', 'size'),
                                                         Q1010_weighted_avg=('Q1010_weighted', 'mean'),
                                                         Q3010_weighted_avg=('Q3010_weighted', 'mean'))

    hbp_reg_data_rs = nba_team_perf_rs.join(hbp_by_team, on=['Team', 'Month'])
    hbp_reg_data_rs = hbp_reg_data_rs.set_index('Team').drop(
        index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
               'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    hbp_reg_rs = LinearRegression()
    hbp_reg_rs.fit(hbp_reg_data_rs[['games won', 'win %', 'cum. games won', 'cum. win %']], hbp_reg_data_rs[['Q3010_weighted_avg']])
    hbp_reg_rs_sm = sm.OLS(hbp_reg_data_rs[['Q3010_weighted_avg']], sm.add_constant(hbp_reg_data_rs[['games won', 'win %', 'cum. games won', 'cum. win %']])).fit()
    hbp_reg_rs_pred = hbp_reg_rs_sm.predict(sm.add_constant(hbp_reg_data_rs[['games won', 'win %', 'cum. games won', 'cum. win %']]))
    print("HBP regression regular season")
    print(hbp_reg_rs_sm.summary())
    print()
    print()

    hbp_reg_data_po = nba_team_perf_po.join(hbp_by_team, on=['Team', 'Month'])
    hbp_reg_data_po = hbp_reg_data_po.set_index('Team').drop(
        index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
               'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    hbp_reg_po = LinearRegression()
    hbp_reg_po.fit(hbp_reg_data_po[['playoff games']], hbp_reg_data_po[['Q3010_weighted_avg']])
    hbp_reg_po_sm = sm.OLS(hbp_reg_data_po[['Q3010_weighted_avg']], sm.add_constant(hbp_reg_data_po[['playoff games']])).fit()
    hbp_reg_po_pred = hbp_reg_po_sm.predict(sm.add_constant(hbp_reg_data_po[['playoff games']]))
    print("HBP regression playoffs")
    print(hbp_reg_po_sm.summary())
    print()
    print()

    hbp_user_rs = hbp.reset_index().join(nba_team_perf_rs.set_index(['Team', 'Month']), on=['NBA_team', 'nearest_month'])
    hbp_user_po = hbp.reset_index().join(nba_team_perf_po.set_index(['Team', 'Month']), on=['NBA_team', 'nearest_month'])
    hbp_user_rs = hbp_user_rs.dropna()
    hbp_user_po = hbp_user_po.dropna()

    hbp_user_reg_rs = LinearRegression()
    hbp_user_reg_rs.fit(hbp_user_rs[['games won', 'win %']], hbp_user_rs[['Q3010_weighted']])
    hbp_user_reg_rs_sm = sm.OLS(hbp_user_rs[['Q3010_weighted']], sm.add_constant(hbp_user_rs[['games won', 'win %']])).fit()
    hbp_reg_rs_pred = hbp_user_reg_rs_sm.predict(sm.add_constant(hbp_user_rs[['games won', 'win %']]))
    print("HBP user regression regular season")
    print(hbp_user_reg_rs_sm.summary())
    print()
    print()

    hbp_user_reg_po = LinearRegression()
    hbp_user_reg_po.fit(hbp_user_po[['playoff games']], hbp_user_po[['Q3010_weighted']])
    hbp_user_reg_po_sm = sm.OLS(hbp_user_po[['Q3010_weighted']], sm.add_constant(hbp_user_po[['playoff games']])).fit()
    hbp_reg_po_pred = hbp_user_reg_po_sm.predict(sm.add_constant(hbp_user_po[['playoff games']]))
    print("HBP user regression playoffs")
    print(hbp_user_reg_po_sm.summary())
    print()

    luth_user_rs = luth_users.reset_index().join(nba_team_perf_rs.set_index(['Team', 'Month']),
                                         on=['Team', 'Month'])
    luth_user_po = luth_users.reset_index().join(nba_team_perf_po.set_index(['Team', 'Month']),
                                         on=['Team', 'Month'])
    luth_user_rs = luth_user_rs.dropna()
    luth_user_po = luth_user_po.dropna()

    luth_reg_rs = LinearRegression()
    luth_reg_rs.fit(luth_user_rs[['games won', 'win %']], luth_user_rs[['used nba web/app']])
    luth_reg_rs_sm = sm.OLS(luth_user_rs[['used nba web/app']], sm.add_constant(luth_user_rs[['games won', 'win %']])).fit()
    luth_reg_rs_pred = luth_reg_rs_sm.predict(sm.add_constant(luth_user_rs[['games won', 'win %']]))
    print("Luth regression regular season")
    print(luth_reg_rs_sm.summary())
    print()
    print()

    luth_reg_po = LinearRegression()
    luth_reg_po.fit(luth_user_po[['playoff games']], luth_user_po[['used nba web/app']])
    luth_reg_po_sm = sm.OLS(luth_user_po[['used nba web/app']], sm.add_constant(luth_user_po[['playoff games']])).fit()
    luth_reg_po_pred = luth_reg_po_sm.predict(sm.add_constant(luth_user_po[['playoff games']]))
    print("Luth regression playoffs")
    print(luth_reg_po_sm.summary())
    print()
    print()


def scale_by_month(samba_by_team):
    final_scaled_data = pd.DataFrame()
    for month in range(1, 13):
        month_data = samba_by_team[samba_by_team['month_of_yr'] == month]
        scaler = MinMaxScaler()
        month_scaled = scaler.fit_transform(month_data.drop(columns=['team', 'Month', 'month_of_yr']).to_numpy())
        month_scaled = pd.concat([month_data[['team', 'Month', 'month_of_yr']].reset_index(drop=True), pd.DataFrame(month_scaled, columns=[
               'nba games watched unweighted',
               'nba tv shows watched unweighted',
               'nba games watched - unique users unweighted',
               'nba tv shows watched - unique users unweighted', 'nba games watched',
               'nba tv shows watched', 'nba games watched - unique users',
               'nba tv shows watched - unique users', 'num_users',
               'weighted_num_users', 'shows per user', 'games per user',
               '% users watched show', '% users watched game'])], axis=1)
        final_scaled_data = pd.concat([final_scaled_data, month_scaled])
    return final_scaled_data


def round_to_nearest_month(date):
    cur_month = dt.datetime(year=date.year, month=date.month, day=1)
    if date.month != 12:
        next_month = dt.datetime(year=date.year, month=date.month+1, day=1)
    else:
        next_month = dt.datetime(year=date.year+1, month=1, day=1)
    diff1 = date - cur_month
    diff2 = next_month - date
    if diff1 <= diff2:
        return cur_month
    else:
        return next_month


def get_cum_values(df_row):
    if df_row['Part of Season'] != 'Second Half':
        df_row['cum. games won'] = 0
        df_row['cum. games played'] = 0
        df_row['cum. win %'] = 0
    else:
        df_row['cum. win %'] = df_row['cum. games won'] / df_row['cum. games played']
    return df_row


def get_cum_games(games_played_col):
    cum_games_col = [0, 0, 0, 0]
    for i in range(4, len(games_played_col)):
        cum_games = cum_games_col[i-4] + games_played_col[i-4]
        cum_games_col.append(cum_games)
    return cum_games_col


def run_correlations(samba, nba_team_perf_rs, nba_team_perf_po, hbp, luth, luth_users, luth_part_of_season):
    samba_by_team = samba.groupby(['team', 'Month']).sum().reset_index()
    # add shows/games watched per user columns
    samba_by_team['shows per user'] = samba_by_team['nba tv shows watched'] / samba_by_team['weighted_num_users']
    samba_by_team['games per user'] = samba_by_team['nba games watched'] / samba_by_team['weighted_num_users']
    samba_by_team['% users watched show'] = samba_by_team['nba tv shows watched - unique users'] / samba_by_team[
        'weighted_num_users']
    samba_by_team['% users watched game'] = samba_by_team['nba games watched - unique users'] / samba_by_team[
        'weighted_num_users']
    samba_by_team['month_of_yr'] = samba_by_team['Month'].dt.month

    samba_by_team_month_scaled = scale_by_month(samba_by_team)

    rs_reg_data = nba_team_perf_rs.join(samba_by_team.set_index(['team', 'Month']), on=['Team', 'Month'])
    rs_reg_data = rs_reg_data.set_index('Team').drop(index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
                                          'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    rs_corr_samba = rs_reg_data.corr()
    rs_corr_samba_spearman = rs_reg_data.corr(method='spearman')

    # using scaled data
    # instead of scaling use % of people who watched
    # compare % of users who watched game to # of games a team had
    rs_reg_data_s = nba_team_perf_rs.join(samba_by_team_month_scaled.set_index(['team', 'Month']), on=['Team', 'Month'])
    rs_reg_data_s = rs_reg_data_s.set_index('Team').drop(index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
                                          'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    rs_corr_samba_s = rs_reg_data_s.corr()
    rs_corr_samba_spearman_s = rs_reg_data_s.corr(method='spearman')


    po_reg_data = nba_team_perf_po.join(samba_by_team.set_index(['team', 'Month']), on=['Team', 'Month'])
    po_reg_data = po_reg_data.set_index('Team').drop(
        index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
               'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    # group by team, month
    po_corr_samba = po_reg_data.corr()
    po_corr_samba_spearman = po_reg_data.corr(method='spearman')

    # using scaled data
    po_reg_data_s = nba_team_perf_po.join(samba_by_team_month_scaled.set_index(['team', 'Month']), on=['Team', 'Month'])
    po_reg_data_s = po_reg_data_s.set_index('Team').drop(
        index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
               'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    # group by team, month
    po_corr_samba_s = po_reg_data_s.corr()
    po_corr_samba_spearman_s = po_reg_data_s.corr(method='spearman')


    hbp['month'] = hbp['date'].dt.to_period('M')
    hbp['month'] = hbp['month'].dt.to_timestamp()
    hbp['nearest_month'] = hbp['date'].apply(round_to_nearest_month)

    hbp_by_team = hbp.groupby(['NBA_team', 'month']).agg(n=('Q1010', 'size'),
                                                         Q1010_sum=('Q1010_weighted', 'sum'),
                                                         Q3010_sum=('Q3010_weighted', 'sum'),
                                                         Q1030_sum=('Q1030_weighted', 'sum'),
                                                         Q1040_sum=('Q1040_weighted', 'sum'),
                                                         sum_of_weights=('weightvalue', 'sum'))
    hbp_by_team['Q1010_weighted_avg'] = hbp_by_team['Q1010_sum'] / hbp_by_team['sum_of_weights']
    hbp_by_team['Q3010_weighted_avg'] = hbp_by_team['Q3010_sum'] / hbp_by_team['sum_of_weights']
    hbp_by_team['Q1030_weighted_avg'] = hbp_by_team['Q1030_sum'] / hbp_by_team['sum_of_weights']
    hbp_by_team['Q1040_weighted_avg'] = hbp_by_team['Q1040_sum'] / hbp_by_team['sum_of_weights']
    hbp_by_team = hbp_by_team.drop(columns=['Q1010_sum', 'Q3010_sum', 'Q1030_sum', 'Q1040_sum', 'sum_of_weights'])
    hbp_corr_data_rs = nba_team_perf_rs.join(hbp_by_team, on=['Team', 'Month'])
    hbp_corr_data_rs = hbp_corr_data_rs.set_index('Team').drop(
        index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
               'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    # group by team, month
    hbp_corr_rs = hbp_corr_data_rs.corr()
    hbp_corr_rs_spearman = hbp_corr_data_rs.corr(method='spearman')

    hbp_corr_data_po = nba_team_perf_po.join(hbp_by_team, on=['Team', 'Month'])
    hbp_corr_data_po = hbp_corr_data_po.set_index('Team').drop(
        index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
               'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    # group by team, month
    hbp_corr_po = hbp_corr_data_po.corr()
    hbp_corr_po_spearman = hbp_corr_data_po.corr(method='spearman')

    # correlations on hbp data using each individual respondent as data point
    hbp_user_rs = hbp.reset_index().join(nba_team_perf_rs.set_index(['Team', 'Month']), on=['NBA_team', 'nearest_month'])
    hbp_user_po = hbp.reset_index().join(nba_team_perf_po.set_index(['Team', 'Month']), on=['NBA_team', 'nearest_month'])
    hbp_user_rs = hbp_user_rs.dropna()
    hbp_user_po = hbp_user_po.dropna()
    hbp_user_corr_rs = hbp_user_rs.corr()
    hbp_user_corr_rs_spearman = hbp_user_rs.corr(method='spearman')
    hbp_user_corr_po = hbp_user_po.corr()
    hbp_user_corr_po_spearman = hbp_user_po.corr(method='spearman')


    # luth correlations (using individual user responses)
    luth_user_rs = luth_users.reset_index().join(nba_team_perf_rs.set_index(['Team', 'Month']),
                                         on=['Team', 'Month'])
    luth_user_po = luth_users.reset_index().join(nba_team_perf_po.set_index(['Team', 'Month']),
                                         on=['Team', 'Month'])
    luth_user_rs = luth_user_rs.dropna()
    luth_user_po = luth_user_po.dropna()
    luth_user_corr_rs = luth_user_rs.corr()
    luth_user_corr_rs_spearman = luth_user_rs.corr(method='spearman')
    luth_user_corr_po = luth_user_po.corr()
    luth_user_corr_po_spearman = luth_user_po.corr(method='spearman')


    # luth correlations (grouping on part of season instead of month)
    nba_team_perf_rs_1 = copy.copy(nba_team_perf_rs)
    nba_team_perf_rs_1['Part of Season'] = nba_team_perf_rs['Month'].apply(get_part_of_season)
    nba_team_perf_rs_1 = nba_team_perf_rs_1.groupby(['Team', 'Part of Season']).sum().reset_index()
    nba_team_perf_rs_1['win %'] = nba_team_perf_rs_1['games won'] / nba_team_perf_rs_1['games played']
    nba_team_perf_rs_1 = nba_team_perf_rs_1[nba_team_perf_rs_1['Part of Season'] != 'Playoffs']
    nba_team_perf_rs_1['cum. games won'] = nba_team_perf_rs_1['games won'].shift(1)
    nba_team_perf_rs_1['cum. games played'] = nba_team_perf_rs_1['games played'].shift(1)
    nba_team_perf_rs_1 = nba_team_perf_rs_1.apply(get_cum_values, axis=1)

    luth_part_of_season = luth_part_of_season.groupby(['Team', 'Part of Season']).sum().reset_index()

    luth_rs_corr_data = nba_team_perf_rs_1.join(luth_part_of_season.set_index(['Team', 'Part of Season']), on=['Team', 'Part of Season'])
    luth_rs_corr_data = luth_rs_corr_data.set_index('Team').drop(index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
                                          'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    luth_rs_corr_data = luth_rs_corr_data.dropna()

    rs_corr_luth = luth_rs_corr_data.corr()
    rs_corr_luth_spearman = luth_rs_corr_data.corr(method='spearman')

    nba_team_perf_po1 = nba_team_perf_po[nba_team_perf_po['Month'] > '2022-01-01']
    nba_team_perf_po1['Part of Season'] = nba_team_perf_po1['Month'].apply(get_part_of_season)
    nba_team_perf_po1 = nba_team_perf_po1.groupby(['Team', 'Part of Season']).sum().reset_index()
    nba_team_perf_po1 = nba_team_perf_po1[nba_team_perf_po1['Part of Season'] == 'Playoffs']

    luth_po_corr_data = nba_team_perf_po1.join(luth_part_of_season.set_index(['Team', 'Part of Season']), on=['Team', 'Part of Season'])
    luth_po_corr_data = luth_po_corr_data.set_index('Team').drop(index=['Los Angeles Lakers', 'Los Angeles Clippers', 'New York Knicks',
                                          'Brooklyn Nets', 'Toronto Raptors']).reset_index()
    luth_po_corr_data = luth_po_corr_data.dropna()

    po_corr_luth = luth_po_corr_data.corr()
    po_corr_luth_spearman = luth_po_corr_data.corr(method='spearman')



    # luth correlations (group by team instead of by 3-month period)
    nba_team_perf_rs['Team Level'] = nba_team_perf_rs['Team'].apply(get_team_level)
    nba_team_perf_rs = nba_team_perf_rs.groupby(['Month', 'Team Level']).sum().reset_index()
    nba_team_perf_rs['win %'] = nba_team_perf_rs['games won'] / nba_team_perf_rs['games played']
    # cum games played should be sum of games won in previous months
    cum_games_played = get_cum_games(nba_team_perf_rs['games played'])
    nba_team_perf_rs['cum. games played'] = cum_games_played
    nba_team_perf_rs['cum. win %'] = nba_team_perf_rs['cum. games won'] / nba_team_perf_rs['cum. games played']
    nba_team_perf_rs['cum. win %'] = nba_team_perf_rs['cum. win %'].replace(np.nan, 0)

    luth['Team Level'] = luth['Team'].apply(get_team_level)
    luth = luth.groupby(['Team Level', 'Month']).sum().reset_index()

    luth_rs_corr_data = nba_team_perf_rs.join(luth.set_index(['Team Level', 'Month']),
                                              on=['Team Level', 'Month'])
    luth_rs_corr_data = luth_rs_corr_data.set_index('Team Level').drop(
        index=['N/A']).reset_index()
    luth_rs_corr_data = luth_rs_corr_data.dropna()

    rs_corr_luth = luth_rs_corr_data.corr()
    rs_corr_luth_spearman = luth_rs_corr_data.corr(method='spearman')

    nba_team_perf_po['Team Level'] = nba_team_perf_po['Team'].apply(get_team_level)
    nba_team_perf_po = nba_team_perf_po.groupby(['Month', 'Team Level']).sum().reset_index()
    # nba_team_perf_po['win %'] = nba_team_perf_po['games won'] / nba_team_perf_po['games played']
    # # cum games played should be sum of games won in previous months
    # cum_games_played = get_cum_games(nba_team_perf_po['games played'])
    # nba_team_perf_po['cum. games played'] = cum_games_played
    # nba_team_perf_po['cum. win %'] = nba_team_perf_po['cum. games won'] / nba_team_perf_po['cum. games played']
    # nba_team_perf_po['cum. win %'] = nba_team_perf_po['cum. win %'].replace(np.nan, 0)

    luth_po_corr_data = nba_team_perf_po.join(luth.set_index(['Team Level', 'Month']),
                                              on=['Team Level', 'Month'])
    luth_po_corr_data = luth_po_corr_data.set_index('Team Level').drop(
        index=['N/A']).reset_index()
    luth_po_corr_data = luth_po_corr_data.dropna()

    po_corr_luth = luth_po_corr_data.corr()
    po_corr_luth_spearman = luth_po_corr_data.corr(method='spearman')

    print()


if __name__ == '__main__':
    luth_users, luth, samba, hbp, nba_team_perf, samba_total_users, luth_total_users, luth_part_of_season = read_data()
    luth_users, luth, samba, hbp, nba_team_perf_rs, nba_team_perf_po, luth_part_of_season = process_data(luth_users, luth, samba, hbp, nba_team_perf, samba_total_users, luth_total_users, luth_part_of_season)
    run_correlations(samba, nba_team_perf_rs, nba_team_perf_po, hbp, luth, luth_users, luth_part_of_season)
    regression_data = run_regression(samba, hbp, nba_team_perf_rs, nba_team_perf_po, luth_users)
    print()