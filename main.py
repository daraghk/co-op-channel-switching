import random
from traffic_generator import create_set_of_channel_traffics_where_half_the_channels_change_bias_at_random_intervals, create_set_of_channel_traffics_with_changing_biases_at_fixed_intervals, create_set_of_channel_traffics_with_fixed_biases
from air_traffic_data import AirTrafficData
from coop_controller import CoopController

number_of_zero_biased_channels = 4
number_of_one_biased_channels = 4

generated_channel_traffics = create_set_of_channel_traffics_with_changing_biases_at_fixed_intervals(
    0.1, 0.9, number_of_zero_biased_channels, number_of_one_biased_channels, switch_traffic_bias_interval=10)

# generated_channel_traffics = create_set_of_channel_traffics_with_fixed_biases(
#     0.1, 0.9, number_of_zero_biased_channels, number_of_one_biased_channels)

# generated_channel_traffics = create_set_of_channel_traffics_where_half_the_channels_change_bias_at_random_intervals(
#     0.1, 0.9, number_of_biased_one_channels=number_of_one_biased_channels, number_of_biased_zero_channels=number_of_zero_biased_channels, traffic_length=10000)

channel_traffic_data = AirTrafficData(generated_channel_traffics)
coop_layer = CoopController(number_of_radio_units=2,
                            number_of_channels=8,
                            max_channel_cache_size=1024,
                            min_channel_cache_size=32)


def debug_print(current_traffic, current_sensed_values, channel_caches, cache_shape, cache_size):
    print("ALL CURRENT TRAFFIC: ", current_traffic)
    print("CURRENT SENSED VALUES: ", current_sensed_values)
    print("CURRENT CHANNEL CACHES: ", channel_caches)
    print("CURRENT CHANNEL CACHES SHAPE", cache_shape)
    print("CURRENT CACHE SIZE:", cache_size)

correct_count = 0
incorrect_count = 0
smart_switched = False
total_smart_switches = 0
random_score = 0
while channel_traffic_data.time_step < channel_traffic_data.number_of_timesteps:
    current_traffic = channel_traffic_data.get_current_traffic()

    current_sensed_values_from_radio_units = coop_layer.get_current_sensed_channel_values_from_radio_units(
        current_traffic)
    coop_layer.add_all_current_channel_values_to_cache_including_unknowns(
        current_sensed_values_from_radio_units)

    sensed_channel = coop_layer.radio_units[coop_layer.monitored_radio_unit].sensing_channel
    if smart_switched:
        # If smart switched and channel switched to is now 0 then correct += 1
        # if channel switched to now has value 1 and there is a 0 available then incorrect += 1
        # random channel choice and check also included if sensed value is zero then random_score += 1
        total_smart_switches += 1
        sensed_value_from_monitored_radio = current_sensed_values_from_radio_units[sensed_channel]
        if sensed_value_from_monitored_radio == 0:
            correct_count += 1
        elif sensed_value_from_monitored_radio == 1 and 0 in current_traffic:
            incorrect_count += 1

        random_channel_choice = random.randint(0, number_of_one_biased_channels + number_of_zero_biased_channels - 1)
        if current_traffic[random_channel_choice] == 0:
            random_score += 1


    print("Monitored Radio - sensing channel",
          coop_layer.radio_units[coop_layer.monitored_radio_unit].sensing_channel,
           "Current Traffic", current_traffic,
           "MR Cache line", coop_layer.channel_caches.channel_caches[-1],
           "Cache Size", coop_layer.channel_caches.size)
        
    # debug_print(current_traffic=current_traffic,
    #             current_sensed_values=current_sensed_values_from_radio_units,
    #             channel_caches=coop_layer.channel_caches.channel_caches,
    #             cache_shape=coop_layer.channel_caches.cache_shape(),
    #             cache_size=coop_layer.channel_caches.size)

    smart_switched = coop_layer.trigger_radio_unit_switching(current_sensed_values_from_radio_units)

proportion_correct_of_total_smart_switches = correct_count / total_smart_switches
proportion_correct_of_total_smart_switches_ignoring_no_zero_choices = correct_count / (correct_count + incorrect_count)
proportion_random_correct_of_total_smart_switches = random_score / total_smart_switches

print("TOTAL SMART SWITCHES: ", total_smart_switches)
print("CORRECT SMART SWITCHES: ", correct_count)
print("INCORRECT SMART SWITCHES: ", incorrect_count)
print("CORRECT RANDOM SWITCHES: ", random_score)

print("CORRECT SMART PROPORTION: ", proportion_correct_of_total_smart_switches)
print("CORRECT SMART PROPORTION, ignore dead ends: ", proportion_correct_of_total_smart_switches_ignoring_no_zero_choices)
print("CORRECT RANDOM PROPORTION: ", proportion_random_correct_of_total_smart_switches)
print(channel_traffic_data.number_of_timesteps)
print(len(generated_channel_traffics[0]))