import pandas as pd
import numpy as np

from air_traffic_data import AirTrafficData

folder_path = '/home/daragh/Documents/Datasets/CD-RSSI/edited'

# data not of same length for each node - select first X values - may have misalignment
DATA_LENGTH = 100000
COL_HEADER = 'HEAD'
NODE_RANGE = range(1, 17)


def set_up_data():
    all_data = []
    for node_number in NODE_RANGE:
        print(node_number)
        df = None
        # these channel files had char encoding issue in init comment sections
        if node_number == 9 or node_number == 13:
            # df = pd.read_csv(folder_path + "/node" + str(node_number) + ".txt", skiprows=14, comment='#')
            # nodes 9 and 13 have some corrupt values - ignore for now
            pass
        else:
            df = pd.read_csv(folder_path + "/node" +
                             str(node_number) + ".txt", skiprows=19, comment='#')

        if df is not None:
            print(df.columns)
            series = df.iloc[:, 0][:DATA_LENGTH]
            series_as_array = np.array(series, dtype=int)
            series_as_array = np.where(series_as_array < 30, 1, 0)
            all_data.append(series_as_array)
            print(max(series_as_array), min(series_as_array))
            print(series_as_array, len(series_as_array))

    all_data = np.array(all_data)
    print(all_data.shape)

    rss_data_final = AirTrafficData(all_data)
    print(rss_data_final.traffic_data)
    print(rss_data_final.traffic_data.shape)
    return rss_data_final
