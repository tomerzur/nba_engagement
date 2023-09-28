# nba_engagement
In this project I measure the impact of NBA team performance on fan engagement.

In this repository I have aggregated data sets from three data sources (Luth, Samba, and the Harris Brand Platform). I have also included my abstract submission to the Sloan Sports Conference ([NBA project abstract.docx](NBA%20project%20abstract.docx)), an interactive Tableau dashboard that can be used to explore the data and results from the project ([NBA data report.twb](NBA%20data%20report.twb)), a short powerpoint deck summarizing the findings of my project ([NBA Project presentation condensed.pptx](NBA%20Project%20presentation%20condensed.pptx)), and the code I used for this project. Note that the code (located in the [analyses](analyses) folder) uses user-level data which I didn't include due to licensing concerns.

### Data
Here is a short description of each data file I have included. Note that these files are all used in the NBA data report Tableau dashboard.

[correlations.csv](correlations.csv) - all of the correlations I calculated between team performance and each of the luth/samba/harris brand platform metrics. These correlations are calculated based on data points taken at the region/monthly level, and can be explored in the "Correlations" and "Correlations (visual)" tabs of the Tableau dashboard.

[hbp_data.csv](hbp_data.csv) - data from the Harris Brand Platform. This data is aggregated at the team/month level, and can be explored more in the "Harris Brand Platform time series" tab of the Tableau dashboard.

[luth_data.csv](luth_data.csv) - data from the Luth metered panel. This data is aggregated at the state/month level, and can be explored more in the "Luth time series" tab of the Tableau dashboard.

[luth_data_to_group.csv](luth_data_to_group.csv) - Luth data, but aggregated at the team/month level.

[samba_data.csv](samba_data.csv) - data from Samba TV. This data is aggregated at the DMA/month level, and can be explored more in the "Samba time series" tab of the Tableau dashboard.

[samba_data_to_group.csv](samba_data_to_group.csv) - Samba data, but aggregated at the team/month level.

[nba_team_perf_po_data.csv](nba_team_perf_po_data.csv) - NBA team performance data from the 2021 and 2022 NBA playoffs.

[nba_team_perf_po_data.csv](nba_team_perf_po_data.csv) - NBA team performance data from the 2021-2022 NBA regular season.
