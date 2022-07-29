import numpy as np


class AirTrafficData:
    def __init__(self, traffic_data):
        """ Traffic data expected in shape of (channels, traffic_length) """
        self.number_of_channels = len(traffic_data)
        self.number_of_timesteps = len(traffic_data[0])
        self.traffic_data = np.array(traffic_data).T
        self.time_step = 0

    def get_current_traffic(self):
        """ Has side effect of incrementing time by 1"""
        current_traffic = self.traffic_data[self.time_step]
        if self.time_step < self.number_of_timesteps:
            self.time_step += 1
        return current_traffic
