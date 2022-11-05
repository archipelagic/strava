# Analyzing Strava data with Python

This repo is dedicated to analyzing sports activties with a tracking software such as Strava. Most if not all of these trackers allow you to download a temporary snapshot of your activity data, and while the often also offer APIs to interact with, here I focus on a static analysis. The goal is to provide someone who has never worked with GPX files to get started exploring the vast possibility offered by this type of data (see `analyzing_one_activity`). In addition, I've also written some code to get a high-level overview of your activities. The notebook for this is called `all_activities`.

Helper functions are stored in two Python files; `plot_helpers.py` for graphs and `format_data.py` to transform the data. All the data that is used or generated in the process will be located inside the `data` folder.

For more detailed explanations of how to interact with the code, I've written up two articles providing context and illustrations: [Part 1](https://medium.com/swlh/getting-the-most-out-of-your-sports-tracker-fac87b1d242b) and [Part 2](https://towardsdatascience.com/getting-the-most-out-of-your-tracking-app-part-ii-gps-analysis-30a7eaa0a19).
