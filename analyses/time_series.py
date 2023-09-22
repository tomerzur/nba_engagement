import copy
import numpy as np
import pandas as pd
from matplotlib import pyplot
from prophet import Prophet
from prophet.plot import plot_forecast_component, plot
from statsmodels.tsa.arima.model import ARIMA

if __name__ == '__main__':
    watch_data = pd.read_csv('../samba_data.csv')
    watch_data_by_team = watch_data.groupby(by=['team','Month']).sum().reset_index()
    teams = ['Atlanta Hawks', 'Boston Celtics', 'Charlotte Hornets', 'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks',
             'Denver Nuggets', 'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers', 'Memphis Grizzlies',
             'Miami Heat', 'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'No Team', 'Oklahoma City Thunder',
             'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns', 'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs',
             'Unsure', 'Utah Jazz', 'Washington Wizards']
    dates_to_predict = pd.DataFrame(
        ['2022-11-01', '2022-12-01', '2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01',
         '2023-06-01', '2023-07-01', '2023-08-01', '2023-09-01', '2023-10-01', '2023-11-01', '2023-12-01'],
        columns=['ds'])
    dates_to_predict['ds'] = pd.to_datetime(dates_to_predict['ds'], format='%Y-%m-%d')
    # dates_to_predict['cap'] = 10000000
    # dates_to_predict['floor'] = 0
    preds_by_team = copy.copy(dates_to_predict)
    preds_by_team_a = copy.copy(dates_to_predict)
    for team in teams:
        team_watch_data = watch_data_by_team[watch_data_by_team['team'] == team]
        team_watch_data = team_watch_data[['Month', 'nba games watched']].rename(columns={'Month': 'ds',
                                                                                            'nba games watched': 'y'})
        # team_watch_data['cap'] = 10000000
        # team_watch_data['floor'] = 0

        model = Prophet(yearly_seasonality=True)
        model.fit(team_watch_data, iter=250)
        test_pred = model.predict(dates_to_predict)
        preds_by_team[team] = test_pred['yhat'].apply(lambda x: 0 if x < 0 else x)

        model_a = ARIMA(np.asarray(team_watch_data['y']), order=(8, 1, 0))
        model_a1 = model_a.fit()
        preds = model_a1.forecast(steps=14)
        preds_by_team_a[team] = preds

    preds_by_team = preds_by_team.T

    hawks_watch_data = watch_data_by_team[watch_data_by_team['team'] == 'Atlanta Hawks']
    hawks_watch_data = hawks_watch_data[['Month', 'nba games watched']].rename(columns={'Month': 'ds',
                                                                                        'nba games watched': 'y'})
    # hawks_watch_data['cap'] = 10000000
    # hawks_watch_data['floor'] = 0
    celtics_watch_data = watch_data_by_team[watch_data_by_team['team'] == 'Boston Celtics']
    celtics_watch_data = celtics_watch_data[['Month', 'nba games watched']].rename(columns={'Month': 'ds',
                                                                                        'nba games watched': 'y'})
    # celtics_watch_data['cap'] = 10000000
    # celtics_watch_data['floor'] = 0
    model = Prophet(yearly_seasonality=True)
    model.fit(hawks_watch_data, iter=250)

    test_pred = model.predict(dates_to_predict)

    model2 = Prophet(yearly_seasonality=True)
    model2.fit(celtics_watch_data, iter=250)
    test_pred2 = model2.predict(dates_to_predict)


    fig = pyplot.figure(figsize=(12, 8))
    ax1 = fig.add_subplot(2, 2, 1)
    plot(m=model, fcst=test_pred, ax=ax1)
    ax1.set_title('Hawks time series')

    ax2 = fig.add_subplot(2, 2, 2)
    plot(m=model2, fcst=test_pred2, ax=ax2)
    ax2.set_title('Celtics time series')

    ax3 = fig.add_subplot(2, 2, 3)
    plot(m=model2, fcst=test_pred2, ax=ax3)
    ax3.set_title('Celtics time series')

    ax4 = fig.add_subplot(2, 2, 4)
    plot(m=model2, fcst=test_pred2, ax=ax4)
    ax4.set_title('Celtics time series')

    pyplot.show()

    preds_by_team.to_csv('time_series_forecast.csv')
    print()
    print()