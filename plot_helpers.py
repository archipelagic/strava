import seaborn as sns
import matplotlib.pyplot as plt

class plotting:
    
    def plot_histograms(df, category = 'distance'):
        
        # create local df to manipulate if needed
        plot_df = df.copy()
        # convert timedelta back to float to allow for plotting
        if (category =='moving_time' or category == 'elapsed_time'):
            plot_df[category] = plot_df[category].astype('timedelta64[s]') / 3600
            
        g = sns.FacetGrid(data = plot_df, col="type", col_wrap = 2, sharex = False, height = 6)
        g.map(sns.histplot, category)
        g.fig.suptitle(f'Histogram for {category}', y=1.05)
        
    def plot_regression(df, type_of_activity, x, y):
        
        # create local df to manipulate if needed
        plot_df = df.copy()
        
        if (x =='moving_time' or x == 'elapsed_time'):
            plot_df[x] = plot_df[x].astype('timedelta64[s]') / 3600
        elif (y =='moving_time' or y == 'elapsed_time'):
            plot_df[y] = plot_df[y].astype('timedelta64[s]') / 3600
        
        activity = plot_df[plot_df.type == type_of_activity]
        g = sns.regplot(data = activity, x=x, y=y)
        g.figure.set_size_inches(10, 10)
        sns.despine()
        plt.title(f'Regression for {x} vs. {y}')
        
        
    def plot_scatter(df, x, y):
        
        # create local df to manipulate if needed
        plot_df = df.copy()
        
        if (x =='moving_time' or x == 'elapsed_time'):
            plot_df[x] = plot_df[x].astype('timedelta64[s]') / 3600
        elif (y =='moving_time' or y == 'elapsed_time'):
            plot_df[y] = plot_df[y].astype('timedelta64[s]') / 3600
        
        g = sns.scatterplot(data = plot_df, x = x, y = y, hue = 'type')
        g.figure.set_size_inches(10, 10)
        sns.despine()
        plt.title("Scatterplot for all types of activities")
        
        
    def plot_multi_reg(df, x, y):
        
        # create local df to manipulate if needed
        plot_df = df.copy()
        
        if (x =='moving_time' or x == 'elapsed_time'):
            plot_df[x] = plot_df[x].astype('timedelta64[s]') / 3600
        elif (y =='moving_time' or y == 'elapsed_time'):
            plot_df[y] = plot_df[y].astype('timedelta64[s]') / 3600
        
        sns.lmplot(data = plot_df, x=x, y=y, hue="type", 
                       markers=["o", "*", "+"], palette="Set1", height = 7)
        
        plt.title(f"Regression for {x} vs {y}, multiple activities")
        
        
    def overlay_map(df, img_loc):
        
        extent = [min(df['longitude']), max(df['longitude']),
                  min(df['latitude']), max(df['latitude'])]
        fig, ax = plt.subplots(figsize=(15, 20))
        
        img = plt.imread(img_loc)
        ax.imshow(img, extent = extent)
        
        ax.scatter(df['longitude'], df['latitude'], color = 'blue', marker = "+", s = 2)
        
    def single_scatter(df, x, y, color):
        g = sns.scatterplot(data = df, x = x, y = y, color = color)
        g.figure.set_size_inches(10, 10)
        
        sns.despine()
        plt.title(f"{x} vs {y} scatterplot")
        
    def smoothed_plot(df, kind = 'pace'):
        
        fig2, ax2 = plt.subplots(figsize=(15, 5))
        
        plt.scatter(df['distance'],df[kind], label = f'Raw {kind} data', s = 10, marker = 'x')
        plt.plot(df['distance'],df[f'{kind}_smooth'], color='red', label = 'After smoothing out')
        
        plt.legend()
        plt.show()
        
    def plot_aggregate_by_type(df, category = 'distance'):

        df_copy = df.copy()
        
        #get elapsed time in hours
        if (category == 'moving_time' or category == 'elapsed_time'):
            df_copy[f'{category}_cum'] = df_copy[f'{category}_cum'].astype('timedelta64[s]') / 3600
        
        g = sns.lineplot(data = df_copy, x = 'date', y = f'{category}_cum', hue = 'type')
        g.figure.set_size_inches(10, 10)
        sns.despine()
        plt.title(f"Progression over time for {category}")
        
    def plot_aggregate_by_year(df, category = 'distance'):
    
        df_copy = df.copy()
        
        #get elapsed time in hours
        if (category == 'moving_time' or category == 'elapsed_time'):
            df_copy[f'{category}_cum'] = df_copy[f'{category}_cum'].astype('timedelta64[s]') / 3600
        
        g = sns.lineplot(data = df_copy, x = 'dayofyear', y = f'{category}_cum', hue = 'year', palette = 'deep')
        g.figure.set_size_inches(10, 10)
        sns.despine()
        plt.title(f"Yearly progression, all activities, for {category}")

         