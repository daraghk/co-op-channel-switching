import random
import unittest
from channel_caches import EMPTY, UNKNOWN
from radio_unit import RadioUnit


class SwitchController:
    def __init__(self):
        self.number_of_smart_switches = 0
        self.random_smart_switch_mod_criteria = 10

    def smart_switch_channel_for_radio_unit(self, all_radio_units, active_radio_index, joint_channel_value_map, channel_caches, number_of_channels):
        """Given all radio units, find the active radio's best channel to switch to, 
        i.e most likely to be empty and switch (if it is not a random smart switch).
        This channel could already be owned by a passive radio unit, 
        in this case the active and passive radio units swap sensing channels."""
        active_radio_unit = all_radio_units[active_radio_index]
        current_sensed_channel = active_radio_unit.sensing_channel

        best_channel = None
        if self.__is_random_smart_switch():
            print("RANDOM SMART SWITCH")
            best_channel = random.randint(0, number_of_channels - 1)
            while best_channel == current_sensed_channel:
                best_channel = random.randint(0, number_of_channels - 1)
        else:
            best_channel = self.find_best_channel_to_switch_to(
                current_sensed_channel, joint_channel_value_map, channel_caches, number_of_channels)

        for radio_unit in all_radio_units:
            if radio_unit.sensing_channel == best_channel:
                radio_unit.sensing_channel = current_sensed_channel
                break
        active_radio_unit.sensing_channel = best_channel

    def __is_random_smart_switch(self):
        return self.number_of_smart_switches % self.random_smart_switch_mod_criteria == 0

    def find_best_channel_to_switch_to(self, current_sensed_channel, joint_channel_value_map, channel_caches, number_of_channels):
        """ For each channel in the joint_channel_value_map that is unknown at (t),
        calculate the conditonal probability that the channel is empty at the next time step,
        choose the channel with the highest probability"""
        max_conditional_probability = 0
        channel_to_switch_to = current_sensed_channel
        for channel in range(number_of_channels):
            if joint_channel_value_map[channel] == UNKNOWN:
                conditional_probability = self.calculate_conditional_probability(
                    channel, joint_channel_value_map, channel_caches)
                if conditional_probability > max_conditional_probability:
                    max_conditional_probability = conditional_probability
                    channel_to_switch_to = channel
            elif joint_channel_value_map[channel] == EMPTY:
                channel_to_switch_to = channel
                break
        return channel_to_switch_to

    def immediate_switch_channel_for_all_radio_units(self, radio_units, number_of_channels):
        """Increments all radio unit sensing channel numbers by 1 """
        for radio_unit in radio_units:
            next_channel = radio_unit.sensing_channel + 1
            if next_channel == number_of_channels:
                radio_unit.sensing_channel = 0
            else:
                radio_unit.sensing_channel = next_channel

    def calculate_conditional_probability(self, channel_to_check, joint_channel_value_map, channel_caches):
        """ Calculates the conditional probability that channel_to_check at (t+1) is EMPTY, 
        given the joint_channel_value_map for (t)"""
        numerator = 0
        denominator = 0
        last_channel_cache_index = len(channel_caches) - 1
        for i in range(len(channel_caches)):
            cache_row = channel_caches[i]
            if self.__check_all_channel_values_in_cache_row(cache_row, joint_channel_value_map):
                denominator += 1
                next_cache_row_valid = True if i != last_channel_cache_index else False
                if next_cache_row_valid:
                    next_cache_row = channel_caches[i+1]
                    if next_cache_row[channel_to_check] == EMPTY:
                        numerator += 1
        return numerator / denominator if denominator != 0 else 0

    def joint_channel_values_count(self, channel_caches, joint_channel_value_map):
        """ Iterates over each cache row, 
        checks if all channel values from channel_value_map are in the row
        if all are present -> increment count by 1"""
        count = 0
        for cache_row in channel_caches:
            count_row = self.__check_all_channel_values_in_cache_row(
                cache_row, joint_channel_value_map)
            if count_row:
                count += 1
        return count

    def __check_all_channel_values_in_cache_row(self, cache_row, joint_channel_value_map):
        result = True
        for channel in joint_channel_value_map.keys():
            if cache_row[channel] != joint_channel_value_map[channel]:
                result = False
                break
        return result


class TestCalculationFunctions(unittest.TestCase):
    def setUp(self):
        self.switch_controller = SwitchController()

    def test_joint_channel_values_count(self):
        channel_caches = [[1, 0, 1], [1, 0, 0], [0, 0, 1]]
        channel_value_map = {0: 1, 1: 0}
        result = self.switch_controller.joint_channel_values_count(
            channel_caches, channel_value_map)
        self.assertEqual(result, 2)

    def test_joint_channel_values_count_empty(self):
        channel_caches = [[1, 0, 1], [1, 0, 0], [0, 0, 1]]
        channel_value_map = {0: 4, 1: 5}
        result = self.switch_controller.joint_channel_values_count(
            channel_caches, channel_value_map)
        self.assertEqual(result, 0)

    def test_calculate_conditional_probability(self):
        channel_caches = [[1, 0, 1], [0, 0, 1], [0, 1, 0], [1, 0, 1]]
        channel_value_map = {1: 0, 2: 1}
        result = self.switch_controller.calculate_conditional_probability(
            channel_to_check=0, joint_channel_value_map=channel_value_map, channel_caches=channel_caches)
        self.assertEqual(result, 2/3.)

    def test_find_best_channel_for_switch_when_empty_available_in_passive(self):
        channel_caches = [[1, 0, 1, 0], [
            0, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 1]]
        channel_value_map = {0: 2, 1: 0, 2: 1, 3: 2}
        number_of_channels = 4
        current_sensed_channel = 0
        result = self.switch_controller.find_best_channel_to_switch_to(
            current_sensed_channel, channel_value_map, channel_caches, number_of_channels)
        self.assertEqual(result, 1)

    def test_find_best_channel_for_switch_when_no_empty_available_in_passive(self):
        channel_caches = [[1, 0, 1, 0], [
            0, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 1]]
        channel_value_map = {0: 2, 1: 1, 2: 1, 3: 2}
        number_of_channels = 4
        current_sensed_channel = 0
        result = self.switch_controller.find_best_channel_to_switch_to(
            current_sensed_channel, channel_value_map, channel_caches, number_of_channels)
        self.assertEqual(result, 0)

    def test_smart_switch_channel_for_radio_unit(self):
        all_radio_units = []
        number_of_channels = 4
        for i in range(number_of_channels):
            all_radio_units.append(RadioUnit(i))
        active_radio_unit_index = 0
        channel_caches = [[1, 0, 1, 0], [
            0, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 1]]

        # below 1 is available
        # expected behaviour is that the active radio will take this channel and the passive will take the active prev channel, 0
        channel_value_map = {0: 2, 1: 0, 2: 1, 3: 2}

        self.assertEqual(
            all_radio_units[active_radio_unit_index].sensing_channel, 0)
        self.switch_controller.smart_switch_channel_for_radio_unit(all_radio_units=all_radio_units, active_radio_index=active_radio_unit_index,
                                                                                                   joint_channel_value_map=channel_value_map, channel_caches=channel_caches, number_of_channels=number_of_channels)

        self.assertNotEqual(
            all_radio_units[active_radio_unit_index].sensing_channel, 0)