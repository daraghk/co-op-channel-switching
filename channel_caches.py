import numpy as np
import unittest

'''Channel Occupancy Constants'''
EMPTY = 0
OCCUPIED = 1
UNKNOWN = 2


class ChannelCaches:
    def __init__(self, number_of_channels, max_size):
        self.number_of_channels = number_of_channels
        self.channel_caches = self.__init_channel_caches()
        self.size = 0
        self.max_size = max_size

    def __init_channel_caches(self):
        return np.empty(shape=(0, self.number_of_channels))

    def flush_cache(self):
        self.channel_caches = self.__init_channel_caches()
        self.size = 0

    def cache_shape(self):
        return self.channel_caches.shape

    def add_all_current_channel_values_to_cache(self, sensed_channel_values):
        """ Expects sensed_channel_values as dict {channel : sensed_value}.
        Flushes Cache when it reaches max_size.
        Appends all the current channel values to the end of channel_caches, includes unknown values and sensed values """
        if self.size == self.max_size:
            self.flush_cache()

        new_cache_row = np.zeros((1, self.number_of_channels))
        for channel, sensed_value in sensed_channel_values.items():
            new_cache_row[0][channel] = sensed_value
        for channel in range(self.number_of_channels):
            if channel not in sensed_channel_values.keys():
                new_cache_row[0][channel] = UNKNOWN
        self.channel_caches = np.vstack([self.channel_caches, new_cache_row])
        self.size += 1


class TestChannelCaches(unittest.TestCase):
    def setUp(self):
        self.number_of_channels = 6
        self.max_size = 42
        self.channel_caches = ChannelCaches(
            self.number_of_channels, self.max_size)

    def test_channel_caches_init(self):
        cache_shape = self.channel_caches.cache_shape()
        rows = cache_shape[0]
        cols = cache_shape[1]
        self.assertEqual(rows, 0)
        self.assertEqual(cols, self.number_of_channels)

    def test_add_all_current_channel_values_to_cache(self):
        sensed_channel_value_map = {0: 1, 1: 1}
        original_cache_size = self.channel_caches.size
        self.channel_caches.add_all_current_channel_values_to_cache(
            sensed_channel_value_map)
        new_cache_size = self.channel_caches.size
        self.assertEqual(new_cache_size, original_cache_size + 1)

        unknown_channel_value = 2
        last_cache_row_inserted = self.channel_caches.channel_caches[-1]
        for channel in range(len(last_cache_row_inserted)):
            # if channel was sensed then check cached value versus known in current_traffic
            if channel in sensed_channel_value_map.keys():
                self.assertEqual(
                    sensed_channel_value_map[channel], last_cache_row_inserted[channel])
            # channel was not sensed, ensure value cached indicates unknown
            else:
                self.assertEqual(
                    last_cache_row_inserted[channel], unknown_channel_value)

    def test_auto_cache_flushing(self):
        for i in range(self.max_size + 10):
            sensed_channel_value_map = {0: 1, 1: 1}
            self.channel_caches.add_all_current_channel_values_to_cache(
                sensed_channel_value_map)

        self.assertTrue(self.channel_caches.size <
                        self.channel_caches.max_size)
        self.assertTrue(len(self.channel_caches.channel_caches)
                        < self.channel_caches.max_size)
