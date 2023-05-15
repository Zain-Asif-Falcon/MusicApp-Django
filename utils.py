import mutagen


def parse_duration(length):
    hours = length // 3600  # calculate in hours
    length %= 3600
    mins = length // 60  # calculate in minutes
    length %= 60
    seconds = length  # calculate in seconds

    return mins, seconds  # returns the duration


def song_duration(file):
    file_info = mutagen.File(file).info
    length = int(file_info.length)
    mins, seconds = parse_duration(length)
    return f"{mins:02}:{seconds:02}"


