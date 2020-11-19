import pandas as pd
import haversine
import scipy.signal
from timezonefinder import TimezoneFinder
from datetime import timezone, date
import pytz
pd.options.mode.chained_assignment = None  # disable warning

class format_df:
    
    def prepare_activities(self, df):
        df = self.drop_and_rename_cols(df)
        df = self.format_cols(df)
        #make sure they're sorted chronologically
        df.sort_values(by = 'date', inplace = True)
        # Adapt to your language and usage
        return self.select_and_rename_activities(df, ['Run', 'Ride', 'Hike'],
                                          ['running', 'cycling', 'hiking'])
        
    
    def drop_and_rename_cols(self, df):
        
        # Depending on your language, you might have to change this list
        col_names_old = ['Activity ID', 'Activity Date', 'Activity Type', 'Distance', 
                         'Moving Time', 'Elapsed Time', 'Max Speed', 
                         'Elevation Gain', 'Max Grade']
        
        col_names_new = ['id', 'date', 'type', 'distance', 'moving_time', 
                          'elapsed_time', 'max_speed',  'elevation', 'max_incline']
        
        #create dictionary to translate column names to english
        translation_dict = self.create_translation_dict(col_names_old, col_names_new)

        #filter only columns we want to keep
        df = df[col_names_old]
        
        #return renamed columns
        return df.rename(columns = translation_dict)
    
    def format_cols(self, df):
        
        df['distance'] = pd.to_numeric(df['distance'].str.replace(',', '.', regex=False))
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        
        # add column with average speed in m/s (Strava data often NaN)
        df['avg_speed'] = (1000 * df['distance']/df['moving_time']).round(1)
        
        # Change time datetime format
        df['elapsed_time'] = pd.to_timedelta(df['elapsed_time'].astype(int), unit = 'sec')
        df['moving_time'] = pd.to_timedelta(df['moving_time'].astype(int), unit = 'sec')
        
        #Some activties were manually entered and data is missing. Should be filled before other calculations!
        df.fillna(0.0, inplace = True)
        
        # Add kilometer effort metric (distance in km + elevation gain in 100m)
        df['km_effort'] = (df['distance'] + df['elevation'].div(100)).round(2)
        
        # Average incline for activity
        df[['max_incline', 'elevation']] = df[['max_incline', 'elevation']].round(1)
        df['avg_incline'] = (df['elevation']/(10*df['distance'])).round(1)
        
        df.set_index('id', inplace = True)
        
        return df
        
        
    def select_and_rename_activities(self, df, orig_names, new_names):
        
        transl_dict = self.create_translation_dict(orig_names, new_names)
        
        df = df[df['type'].isin(orig_names)]
        df['type'] = df['type'].replace(transl_dict)
        
        return df
        
    def create_translation_dict(self, orig_names, new_names):
        
        trans_dict =  {orig_name : new_name for (orig_name, new_name) 
                            in zip(orig_names, new_names)}
        
        return trans_dict
    
    
    def create_aggregate_copy(df, group = 'type', saveToFile = True):
        
        #Create local copy
        df_copy = df.copy()
        
        for col in ['distance', 'elevation', 'km_effort', 'moving_time', 'elapsed_time']:          
            df_copy[f'{col}_cum'] = df_copy.groupby(group)[col].cumsum(numeric_only=False)
        
        if(group == 'year'):
            df_copy['dayofyear'] = df_copy['date'].apply(lambda x: x.dayofyear)
            
        if (saveToFile):
            df_copy.to_csv(f'data/activities_cum_by_{group}.csv')
            
        return df_copy      

class format_gpx:
    
    def get_df_from_gpx(self, gpx_file):

        segment = (gpx_file.tracks[0]).segments[0]
        start = segment.points[0]
        preceding_point = start
        
        data = []
        dist_cumul = 0
        vertical_gain = 0
        vertical_loss = 0
        
        # Times/dates are in UTC, we need to address that
        tf = TimezoneFinder()          
        
        for point_idx, point in enumerate(segment.points):
            
            dist_cumul  += self.calculate_distance(point, preceding_point)
            
            elevation_tuple = self.calculate_elevation(point, preceding_point)
            vertical_gain +=elevation_tuple[0]
            vertical_loss +=elevation_tuple[1]
            
            timezone_str = tf.timezone_at(lng = point.longitude, lat = point.latitude)
            timezone = pytz.timezone(timezone_str)

            #reassigne the immediately preceding point
            preceding_point = point
               
            data.append([point.elevation,
                         point.longitude,
                         point.latitude,
                         segment.get_speed(point_idx),
                         self.utc_to_local(point.time, timezone),
                         timezone,
                         point.time - start.time,
                         dist_cumul,
                         vertical_gain,
                         vertical_loss
                        ])
            
        columns = ['altitude', 'longitude', 'latitude', 'pace', 'time_of_day','time_zone','elapsed_time', 'distance', 
                   'vertical_gain', 'vertical_loss']
        
        df =  pd.DataFrame(data, columns=columns)
        
        # Add two more columms - the current kilometer and the current hour
        df['km'] = df['distance'].astype(int) + 1
        df['hour_of_day'] = pd.to_datetime(df['time_of_day']).dt.hour
        
        return df
    
    def utc_to_local(self, utc_dt, local_tz):
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=local_tz)
    
    def calculate_distance(self, current_point, previous_point):
        
        # Using the haversine metric to calculate the distance between two points
        return haversine.haversine((previous_point.latitude, previous_point.longitude), 
                                            (current_point.latitude, current_point.longitude))
    
    
    def calculate_elevation(self, current_point, previous_point):
        
        vertical_gain = 0
        vertical_loss = 0

        altitude_diff = current_point.elevation - previous_point.elevation
            
        if altitude_diff > 0 :
            vertical_gain = altitude_diff
        elif altitude_diff < 0:
            vertical_loss = abs(altitude_diff)
            
        return (vertical_gain, vertical_loss)
    
    
    #Adding columns with smoothed-out values, using Savitzky-Golay filter
    def add_smooth_cols(self, df):
        
        df['altitude_smooth'] = scipy.signal.savgol_filter(df['altitude'], 51, 3) # window size 51, polynomial order 3
        df['pace_smooth'] = scipy.signal.savgol_filter(df['pace'], 51, 3) 
        df['min_per_km'] = 60/(3.6*df['pace_smooth'])
        
        return df
    
    # Smooths out the vertical gain and loss and adds these columns to the df
    def adjust_vertical(self, df, epsilon = 0.0):
        
        vertical_gain = []
        vertical_loss = []
        
        count_pos = 0.0
        count_neg = 0.0
        
        init_alt = df['altitude_smooth'][0]
        
        for alt in df['altitude_smooth']:
            
            alt_diff = alt - init_alt
            
            # Case 1: We have a significant positive gain
            if alt_diff > epsilon:
                count_pos += alt_diff
            # Case 2: We have a significant negative gain
            elif alt_diff < -epsilon:
                count_neg += abs(alt_diff)
                
            vertical_gain.append(count_pos)
            vertical_loss.append(count_neg)
            
            init_alt = alt
        
        df['vertical_gain_smooth'] = vertical_gain
        df['vertical_loss_smooth'] = vertical_loss
        
        return df
    
    def coarse_grain_activity(df):
        
        # Dictionary that lists the functions according to which we'll group the columns
        grouping_dict = {'distance': 'max',
                 'altitude': 'max',
                 'altitude_smooth': 'min',
                 'pace': 'mean',
                 'hour_of_day': 'min',
                 'elapsed_time':'max',
                 'vertical_gain': 'max',
                 'vertical_loss': 'max',
                 'vertical_gain_smooth': 'max',
                 'vertical_loss_smooth': 'max',
                 'min_per_km': 'mean'}
        
        # Create new coarse-grained df
        new_df = df.groupby(by = 'km').agg(grouping_dict)
        
        #some aesthetics
        new_df.rename(columns = {'altitude': 'alt_max', 'altitude_smooth': 'alt_min'}, inplace = True)
        cols_to_round = ['alt_min',  'vertical_gain_smooth', 'vertical_loss_smooth']
        new_df[cols_to_round] = new_df[cols_to_round].round(1)
        new_df[['distance','pace']] = new_df[['distance','pace']].round(2)
        
        # estimate time per km from elapsed time
        new_df['min_per_km_2'] = new_df['elapsed_time'].diff()
        new_df['min_per_km_2'] = new_df['min_per_km_2'].fillna(new_df['elapsed_time'])

        # time per km estimate from pace, transformed into datetime
        new_df['min_per_km'] = pd.to_timedelta((new_df['min_per_km']*60).astype(int), unit = 'sec')
        
        return new_df
    
    
    