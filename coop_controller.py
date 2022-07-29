import unittest
from channel_caches import EMPTY, OCCUPIED, UNKNOWN, ChannelCaches
from radio_unit import RadioUnit
from switch_controller import SwitchController


class CoopController:
    def __init__(self, number_of_radio_units, number_of_channels, max_channel_cache_size, min_channel_cache_size):
        """ Constraints: number_of_radio_units <= number_of_channels
        and max_channel_cache_size must be a multiple of number_of_channels
        and min_channel_cache_size must divide evenly into max_channel_cache_size"""
        self.number_of_channels = number_of_channels
        self.number_of_radio_units = number_of_radio_units
        assert(number_of_radio_units <= number_of_channels)
        assert(max_channel_cache_size % number_of_channels == 0)

        self.radio_units = self.__init_radio_units()
        self.channel_caches = ChannelCaches(
            number_of_channels=number_of_channels, max_size=max_channel_cache_size)
        self.switch_controller = SwitchController()

        self.monitored_radio_unit = 0
        assert(max_channel_cache_size % min_channel_cache_size == 0)
        self.min_channel_cache_size = min_channel_cache_size

    def __init_radio_units(self):
        radio_units = []
        for i in range(self.number_of_radio_units):
            radio_units.append(RadioUnit(i))
        return radio_units

    def get_current_sensed_channel_values_from_radio_units(self, full_current_traffic):
        """ Expects full current traffic row, returns {channel : sensed_value} dict"""
        sensed_channel_values = {}
        for radio_unit in self.radio_units:
            sensed_channel_values[radio_unit.sensing_channel] = full_current_traffic[radio_unit.sensing_channel]
        return sensed_channel_values

    def immediate_switch_channel_for_all_radio_units(self):
        """Increments all radio unit sensing channel numbers by 1 """
        self.switch_controller.immediate_switch_channel_for_all_radio_units(
            self.radio_units, self.number_of_channels)

    def add_all_current_channel_values_to_cache_including_unknowns(self, sensed_channel_values):
        self.channel_caches.add_all_current_channel_values_to_cache(
            sensed_channel_values=sensed_channel_values)

    def trigger_radio_unit_switching(self, current_sensed_values):
        """Triggers logic to switch radio unit channels,
        If currently in a smart switch period and active radio channel is occupied, i.e cache > min cache size then use smart switch logic
        If in smart switch period and channel is empty then continue on this channel
        Else immediate switch all radio unit channels"""
        active_radio_unit = self.radio_units[self.monitored_radio_unit]
        joint_channel_value_map = self.__create_joint_channel_value_map(
            current_sensed_values)

        smart_switched = False
        active_radio_sensed_channel_state = joint_channel_value_map[
            active_radio_unit.sensing_channel]
        smart_switch_period = self.channel_caches.size >= self.min_channel_cache_size

        if smart_switch_period:
            smart_switched = True
            self.switch_controller.number_of_smart_switches += 1
            if active_radio_sensed_channel_state == OCCUPIED:
                self.switch_controller.smart_switch_channel_for_radio_unit(
                        all_radio_units=self.radio_units,
                        active_radio_index=self.monitored_radio_unit,
                        joint_channel_value_map=joint_channel_value_map,
                        channel_caches=self.channel_caches.channel_caches,
                        number_of_channels=self.number_of_channels)
            elif active_radio_sensed_channel_state == EMPTY:
                pass

        if not smart_switched:
            self.switch_controller.number_of_smart_switches = 0
            self.immediate_switch_channel_for_all_radio_units()

        return smart_switched

    def __create_joint_channel_value_map(self, current_sensed_values):
        joint_channel_value_map = current_sensed_values.copy()
        for channel in range(self.number_of_channels):
            if channel not in joint_channel_value_map:
                joint_channel_value_map[channel] = UNKNOWN
        return joint_channel_value_map


class TestCoopController(unittest.TestCase):
    def setUp(self):
        self.number_of_radio_units = 2
        self.number_of_channels = 6
        self.channel_cache_size = 42
        self.coop_controller = CoopController(
            self.number_of_radio_units, self.number_of_channels, self.channel_cache_size, self.channel_cache_size / 6)

    def test_radio_units_added(self):
        self.assertEqual(len(self.coop_controller.radio_units),
                         self.number_of_radio_units)
        for i in range(len(self.coop_controller.radio_units)):
            radio_unit = self.coop_controller.radio_units[i]
            self.assertEqual(i, radio_unit.sensing_channel)

    def test_get_current_sensed_values_from_radio_units(self):
        current_traffic = [1, 0, 0, 1, 0, 1]
        result = self.coop_controller.get_current_sensed_channel_values_from_radio_units(
            current_traffic)
        for radio_unit in self.coop_controller.radio_units:
            result_channel_value = result[radio_unit.sensing_channel]
            real_traffic_channel_value = current_traffic[radio_unit.sensing_channel]
            self.assertEqual(result_channel_value, real_traffic_channel_value)

    def test_immediate_switch_all_radio_unit_channels(self):
        original_sensing_channels = []
        for radio_unit in self.coop_controller.radio_units:
            original_sensing_channels.append(radio_unit.sensing_channel)

        self.coop_controller.immediate_switch_channel_for_all_radio_units()

        new_sensing_channels = []
        for radio_unit in self.coop_controller.radio_units:
            new_sensing_channels.append(radio_unit.sensing_channel)

        self.assertEqual(len(original_sensing_channels),
                         len(new_sensing_channels))
        for i in range(len(original_sensing_channels)):
            self.assertEqual(
                new_sensing_channels[i], original_sensing_channels[i] + 1)

        # set all RUs to last channel to check incrementing to 0
        for radio_unit in self.coop_controller.radio_units:
            radio_unit.sensing_channel = self.number_of_channels - 1
        self.coop_controller.immediate_switch_channel_for_all_radio_units()

        for radio_unit in self.coop_controller.radio_units:
            self.assertEqual(radio_unit.sensing_channel, 0)

    def test_add_all_current_channel_values_to_cache_including_unknowns(self):
        original_cache_size = self.coop_controller.channel_caches.size
        current_traffic = [1, 0, 0, 1, 0, 1]
        sensed_channel_values = self.coop_controller.get_current_sensed_channel_values_from_radio_units(
            current_traffic)
        self.coop_controller.add_all_current_channel_values_to_cache_including_unknowns(
            sensed_channel_values)
        new_cache_size = self.coop_controller.channel_caches.size
        self.assertEqual(new_cache_size, original_cache_size + 1)

        unknown_channel_value = 2
        last_cache_row_inserted = self.coop_controller.channel_caches.channel_caches[-1]
        for channel in range(len(last_cache_row_inserted)):
            # if channel was sensed then check cached value versus known in current_traffic
            if channel in sensed_channel_values.keys():
                self.assertEqual(
                    current_traffic[channel], last_cache_row_inserted[channel])
            # channel was not sensed, ensure value cached indicates unknown
            else:
                self.assertEqual(
                    last_cache_row_inserted[channel], unknown_channel_value)

    def test_trigger_radio_unit_switching_non_smart_switch(self):
        current_traffic = [1, 0, 0, 1, 0, 1]
        sensed_channel_values = self.coop_controller.get_current_sensed_channel_values_from_radio_units(
            current_traffic)
        original_monitored_radio_unit_channel = self.coop_controller.radio_units[
            self.coop_controller.monitored_radio_unit].sensing_channel
        self.assertEqual(original_monitored_radio_unit_channel, 0)

        self.coop_controller.trigger_radio_unit_switching(
            sensed_channel_values)

        new_monitored_radio_unit_channel = self.coop_controller.radio_units[
            self.coop_controller.monitored_radio_unit].sensing_channel
        self.assertEqual(new_monitored_radio_unit_channel,
                         original_monitored_radio_unit_channel + 1)

    def test_trigger_radio_unit_smart_switch(self):
        traffic = [[1, 0, 0, 1, 0, 1],
                   [0, 1, 0, 0, 1, 1],
                   [1, 0, 0, 1, 1, 1],
                   [1, 0, 0, 1, 0, 1],
                   [1, 0, 0, 1, 1, 1],
                   [0, 1, 0, 1, 0, 1],
                   [1, 0, 1, 1, 1, 1],
                   [0, 0, 1, 0, 0, 1],
                   [1, 1, 0, 1, 1, 1],
                   [0, 0, 0, 1, 0, 1]]

        for current_traffic in traffic:
            sensed_channel_values = self.coop_controller.get_current_sensed_channel_values_from_radio_units(
                current_traffic)
            self.coop_controller.add_all_current_channel_values_to_cache_including_unknowns(
                sensed_channel_values)
            self.coop_controller.immediate_switch_channel_for_all_radio_units()

        # radio unit channels are now 4 and 5, with monitored being 4
        print(self.coop_controller.channel_caches.channel_caches)
        self.assertEqual(self.coop_controller.channel_caches.size, 10)
        original_monitored_radio_unit_channel = self.coop_controller.radio_units[
            self.coop_controller.monitored_radio_unit].sensing_channel
        self.assertEqual(original_monitored_radio_unit_channel, 4)

        latest_traffic_line = [1, 0, 1, 1, 1, 1]
        # sensed values are {4:1, 5:1}
        sensed_channel_values = self.coop_controller.get_current_sensed_channel_values_from_radio_units(
            latest_traffic_line)
        self.coop_controller.trigger_radio_unit_switching(
            sensed_channel_values)

        new_monitored_radio_unit_channel = self.coop_controller.radio_units[
            self.coop_controller.monitored_radio_unit].sensing_channel
        self.assertTrue(original_monitored_radio_unit_channel !=
                        new_monitored_radio_unit_channel)
        self.assertTrue(new_monitored_radio_unit_channel !=
                        original_monitored_radio_unit_channel + 1)
        self.assertEqual(new_monitored_radio_unit_channel, 0)
