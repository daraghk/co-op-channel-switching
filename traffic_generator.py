import random

TRAFFIC_LENGTH = 10000

def create_random_channel_traffic(traffic_length):
    traffic = []
    for _ in range(traffic_length):
        traffic.append(random.randint(0, 1))
    return traffic


def create_channel_traffic(traffic_length, mean, std_dev):
    numbers = []
    for _ in range(traffic_length):
        number = random.gauss(mean, std_dev)
        if number >= 0.5:
            numbers.append(1)
        else:
            numbers.append(0)
    return numbers


def create_set_of_channel_traffics_with_fixed_biases(bias_zero, bias_one, number_of_biased_zero_channels, number_of_biased_one_channels, traffic_length=TRAFFIC_LENGTH):
    # bias_zero and bias_one should be > 0 and < 1
    # bias_zero closer to zero implies more likely to be zero
    # bias_one closer to one implies more likely to be one
    biased_zero_traffic = [create_channel_traffic(
        traffic_length, bias_zero, 0.5) for _ in range(number_of_biased_zero_channels)]
    biased_one_traffic = [create_channel_traffic(
        traffic_length, bias_one, 0.5) for _ in range(number_of_biased_one_channels)]
    channels_with_traffic = biased_zero_traffic + biased_one_traffic
    return channels_with_traffic


def create_set_of_channel_traffics_with_changing_biases_at_fixed_intervals(bias_zero, bias_one, number_of_biased_zero_channels, number_of_biased_one_channels, switch_traffic_bias_interval, traffic_length=TRAFFIC_LENGTH):
    beginning_biased_zero_traffic = [create_channel_traffic(
        traffic_length, bias_zero, 0.5) for _ in range(number_of_biased_zero_channels)]
    beginning_biased_one_traffic = [create_channel_traffic(
        traffic_length, bias_one, 0.5) for _ in range(number_of_biased_one_channels)]

    for channel in range(len(beginning_biased_zero_traffic)):
        for step in range(traffic_length):
            if step % (switch_traffic_bias_interval*2) == 0:
                interval_end = step + switch_traffic_bias_interval + 1
                beginning_biased_zero_traffic[channel][step: interval_end] = create_channel_traffic(
                    switch_traffic_bias_interval, bias_one, 0.5)

    for channel in range(len(beginning_biased_one_traffic)):
        for step in range(traffic_length):
            if step % (switch_traffic_bias_interval*2) == 0:
                interval_end = step + switch_traffic_bias_interval + 1
                beginning_biased_one_traffic[channel][step: interval_end] = create_channel_traffic(
                    switch_traffic_bias_interval, bias_zero, 0.5)

    channels_with_traffic = beginning_biased_zero_traffic + beginning_biased_one_traffic
    return channels_with_traffic


def create_set_of_channel_traffics_where_half_the_channels_change_bias_at_random_intervals(bias_zero, bias_one, number_of_biased_zero_channels, number_of_biased_one_channels, traffic_length=TRAFFIC_LENGTH):
    beginning_biased_zero_traffic = [create_channel_traffic(
        traffic_length, bias_zero, 0.5) for _ in range(number_of_biased_zero_channels)]
    beginning_biased_one_traffic = [create_channel_traffic(
        traffic_length, bias_one, 0.5) for _ in range(number_of_biased_one_channels)]

    for channel in range(len(beginning_biased_zero_traffic)):
        for step in range(traffic_length):
            random_number = random.randint(0, 1)
            if random_number > 0.5:
                random_interval_length = random.randint(
                    0, int(traffic_length/4))
                random_interval_end = step + random_interval_length
                if random_interval_end < traffic_length:
                    beginning_biased_zero_traffic[channel][step: random_interval_end] = create_channel_traffic(
                        random_interval_length, bias_one, 0.5)
                    step += random_interval_length

    channels_with_traffic = beginning_biased_zero_traffic + beginning_biased_one_traffic
    return channels_with_traffic
