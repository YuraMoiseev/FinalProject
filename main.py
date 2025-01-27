import librosa
import numpy as np
import matplotlib.pyplot as plt
import parselmouth
from mido import Message, MidiFile, MidiTrack
import os
import math
import crepe
from scipy.io import wavfile
# from pydub import AudioSegment

# note off/on - type

# 96 - one quarter
# for i in range(3, len(Temp3.tracks[0])):
#     print(Temp3.tracks[0][i])
#
# print()
#
# for i in range(3, len(Temp4.tracks[0])):
#     print(Temp4.tracks[0][i])
#
# print()
TIMING_CONST = 24
TIMING_WEIGHT = 0.5
MELODY_WEIGHT = 1 - TIMING_WEIGHT


def present_notes(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        for j in i:
            if hasattr(j, "note") and j.note not in res:
                res.append(j.note)
    return res


def note_sequences(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        res1 = []
        for j in i:
            if hasattr(j, "note") and j.type == "note_on":
                res1.append(j.note)
        res.append(res1)
    return res


def note_sequences1(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        res1 = []
        sub_res1 = []
        for j in range(1, len(i)):
            if hasattr(i[j-1], "note") and i[j-1].type == "note_on":
                sub_res1.append(i[j-1].note)
                if i[j].type == "note_off" or i[j].time != 0:
                    res1.append(sub_res1)
                    sub_res1 = []
        res.append(res1)
    return res


def timing_sequences(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        res1 = []
        time = 0
        for j in i:
            if hasattr(j, "time"):
                time += j.time
                if j.type == "note_on":
                    res1.append(j.time / TIMING_CONST )
                    time = 0
        res.append(res1)
    return res


def paired_sequenses(file):
    a = []
    b = note_sequences(file), timing_sequences(file)
    for i in range(len(b[1])):
        a.append(list(zip(b[0][i], b[1][i])))
    return a


# takes all the tracks from 2 midi files and finds the most similar melody, gives the indexes of melodies and the staring point at which the most suitability was found
# MAIN FUNC FOR NOW!!!
def compare_melodies(file1, file2, melody_length=-1):
    arr1, arr2 = paired_sequenses(file1), paired_sequenses(file2)
    res = (-1, -1), (-1, -1), -1
    for i in range(len(arr1)):
        for j in range(len(arr2)):
            r1 = closest_sequences(arr1[i], arr2[i], melody_length)
            if r1[1] > res[2] or res[2] == -1:
                res = (i, j), r1[0], r1[1]
    return res



# receives instances of series of notes and relative times and finds the most fitting parts
def closest_sequences(arr1, arr2: list, sublength: int):
    if sublength == -1:
        sublength = min(len(arr1), len(arr2))
    if sublength > min(len(arr1), len(arr2)):
        raise Exception(f"Invalid sublist length - {len(arr1)}; {len(arr2)} < {sublength}")
    res = (-1, -1), -1
    for i in range(len(arr1) - sublength + 1):
        for j in range(len(arr1) - sublength + 1):
            help = (arr1[i:i + sublength][0], arr2[j:j + sublength][0]), (arr1[i:i + sublength][1], arr2[j:j + sublength])[1]
            similarity = list_difference(help[0][0], help[0][1]) * MELODY_WEIGHT + list_difference(help[1][0], help[1][1]) * TIMING_WEIGHT
            if similarity < res[1] or res[1] == -1:
                res = (i, j), similarity
    return res


# find the difference between the closest number in the list
# def diff(arr1: list, arr2: list):
#     if (type(arr1) != list):
#         arr1 = [arr1]
#     if (type(arr2) != list):
#         arr2 = [arr2]
#     if len(arr1) < len(arr2):
#         arr1, arr2 = arr2, arr1
#     arr1.sort()
#     arr2.sort()
#     id1, id2 = 0,0
#     sum = 0
#     while id1 < len(arr1) and id2 < len(arr2):
#         if arr1[id1] == arr2[id2]:
#             id1, id2 = id1+1, id2+1
#         elif arr1[id1] > arr2[id2] and arr1[id1] < arr2[id2+1]:
#             sum+= min(abs(arr1[id1]-arr2[id2]), abs(arr1[id1]-arr2[id2+1]))
#             id1 += 1
#         elif arr1[id1] < arr2[id2]:
#             id1+=1
#         elif arr1[id1] > arr2[id2]:
#             id2+=1
#     return sum
def diff(a1, a2):
    return abs(a1 - a2)


def list_difference(arr1: list, arr2: list):
    if len(arr1) != len(arr2):
        raise Exception(f"Invalid list length - {len(arr1)} {len(arr2)}")
    return sum([diff(arr1[i], arr2[i]) for i in range(len(arr1))])







# def mp3_to_wav(file_name, wav_file_name="wav_output"):
#     if file_name[-4:] != ".mp3":
#         raise Exception(f"Invalid file type")
#     sound = AudioSegment.from_mp3(file_name)
#     sound.export("C:/Users/Ymois/PycharmProjects/FinalProject/MusicFiles/Audio/" + wav_file_name, format="wav")
#


# Function to map frequencies to the nearest note
def frequency_to_note_name(frequency):
    if frequency <= 0:
        return None
    A4 = 440.0
    C0 = A4 * pow(2, -4.75)
    h = round(12 * np.log2(frequency / C0))
    octave = h // 12
    n = h % 12
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return f"{note_names[n]}{octave}"


# Restrict note to a specific octave range (e.g., C3 to C4)
def restrict_to_range(note):
    if note is None:
        return None
    note_name, octave = note[:-1], int(note[-1])
    target_octave = octave%8
    return f"{note_name}{target_octave}"


def analyze_parselmouth(file_path, time_step):
    # Parse the sound file
    sound = parselmouth.Sound(file_path)
    pitch = sound.to_pitch(time_step=time_step)

    # Get pitch values and timestamps
    pitch_values = pitch.selected_array['frequency']
    timestamps = np.arange(len(pitch_values)) * pitch.time_step
    return pitch_values, timestamps


def analyze_librosa(file_path, time_step=0.01):
    # Load the audio file
    y, sr = librosa.load(file_path, sr=None)  # sr=None preserves the original sample rate

    # Calculate the corresponding hop length
    hop_length = int(time_step * sr)  # Convert time_step (in seconds) to samples

    # Compute pitch using the piptrack function
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)

    pitch_values = []
    for i in range(pitches.shape[1]):  # Iterate over frames
        pitch = pitches[:, i]
        magnitude = magnitudes[:, i]
        if magnitude.any():  # If there's significant magnitude
            # Find the index of the maximum magnitude in the frame
            max_idx = magnitude.argmax()
            pitch_values.append(pitch[max_idx])

    timestamps = np.arange(len(pitch_values)) * time_step

    # Print pitch values and their corresponding notes
    for pitch in pitch_values:
        print(f"Pitch: {pitch:.2f} Hz -> Note: {frequency_to_note_name(pitch)}")

    return pitch_values, timestamps


def analyze_crepe(file_path, time_step=0.01):

    """
        Analyze the pitch of the audio file using CREPE.

        Parameters:
            file_path (str): Path to the input WAV audio file.
            time_step (float): Time step in seconds for pitch analysis.

        Returns:
            1) In case of mono audio: returns two lists, the first one containing pitch values at all given points in time, the second one containing matching timestamps
            2) In case of stereo audio: returns four lists, first two containing pitch values and timestamps of the right channel, and third and fourth containing the same of the left channel
        """

    # Function to process one channel with CREPE
    def process_channel(channel_data):
        time, frequency, confidence, activation = crepe.predict(
            channel_data,
            sample_rate,
            step_size=int(time_step * 1000),  # Convert seconds to milliseconds
            # model='full'  # Use the full model for better accuracy
        )
        # Filter out low-confidence results (e.g., confidence < 0.5)
        valid_indices = confidence >= 0.5
        return time[valid_indices], frequency[valid_indices]

    # Read the audio file
    sample_rate, audio = wavfile.read(file_path)

    # Check if the audio is mono or stereo, in the first case - analyze right away
    if len(audio.shape) != 2 or audio.shape[1] != 2:
        return process_channel(audio)[1], process_channel(audio)[0], None, None

    # Separate the left and right channels
    left_channel = audio[:, 0]
    right_channel = audio[:, 1]

    # Analyze both channels
    left_timestamps, left_frequencies = process_channel(left_channel)
    right_timestamps, right_frequencies= process_channel(right_channel)

    return right_frequencies, right_timestamps, left_frequencies, left_timestamps


def clean_up_sliding_wnd(data, wnd_length=5, steepness=1):
    def weighted_average(wnd, steepness):
        data = wnd
        for i in range(steepness):
            data = [math.log2(i) for i in data]
        weighted_avr = (sum(data) / len(data))
        for i in range(steepness):
            weighted_avr = 2 ** weighted_avr
        return weighted_avr
    filtered_data = []
    for i in range(len(data)):
        if i < wnd_length // 2:
            wnd = data[0:(1 + i + wnd_length // 2)]
        elif len(data) - i - 1 < wnd_length // 2:
            wnd = data[(i - (wnd_length-1)//2):]
        else:
            wnd = data[i - (wnd_length - 1) // 2:(i + wnd_length // 2 + 1)]
        filtered_data.append(weighted_average(wnd, steepness))
    return filtered_data


def plot_melody(timestamps, pitch_values):
    # Plotting notes over time as horizontal lines
    plt.plot(timestamps, pitch_values, linewidth=0.5)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency")
    plt.title("Detected Frequency Over Time")
    plt.grid(True)
    plt.legend(['Freq'], loc="upper right")
    plt.show()


def create_midi_file(timestamps, pitch_values, lower_limit, upper_limit, midi_file_name):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    # Convert note limits to frequencies
    note_to_freq = {
        'C0': 16.35, 'C1': 32.7, 'C2': 65.41, 'C3': 130.81, 'C4': 261.63, 'C5': 523.25, 'C6': 1046.50, 'C7': 2093, 'C8': 4186.01
    }
    lower_freq = note_to_freq[lower_limit]
    upper_freq = note_to_freq[upper_limit]

    # Create MIDI file
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    # Add MIDI events
    ppq = 500  # Pulses per quarter note
    last_time = 0
    last_note = None

    delta_time = 0
    last_true_note = None

    for t, freq in zip(timestamps, pitch_values):
        if freq == 0 or not (lower_freq <= freq <= upper_freq):
            restricted_note = "-"
            midi_note = None
        else:
            note_name = frequency_to_note_name(freq)
            restricted_note = restrict_to_range(note_name)

            # Convert note name to MIDI note number
            midi_note = note_names.index(restricted_note[:-1]) + (int(restricted_note[-1]) + 1) * 12

        if restricted_note != last_note:
            # Close previous note
            if last_note is not None and last_note != "-" and restricted_note != "-":
                midi_last_note = note_names.index(last_note[:-1]) + (int(last_note[-1]) + 1) * 12
                track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))
                delta_time = 0
                track.append(Message('note_on', note=midi_note, velocity=64, time=round(delta_time)))
                last_true_note = restricted_note

            if last_note is not None and last_note != "-" and restricted_note == "-":
                midi_last_note = note_names.index(last_note[:-1]) + (int(last_note[-1]) + 1) * 12
                track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))
                delta_time = 0

            if last_note == "-" and restricted_note != "-":
                track.append(Message('note_on', note=midi_note, velocity=64, time=round(delta_time)))
                delta_time = 0
            last_note = restricted_note

        # Calculate delta time
        delta_time += (t - last_time) * ppq / (1 / 2)  # Assuming 1/2 seconds per beat for 120 BPM
        last_time = t

    # Close the last note
    if last_note is not None and last_true_note is not None:
        midi_last_note = note_names.index(last_true_note[:-1]) + (int(last_true_note[-1]) + 1) * 12
        track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))

    project_folder = os.getcwd()  # Get the project folder path
    midi_folder = os.path.join(project_folder, "MusicFiles", "Midi")
    os.makedirs(midi_folder, exist_ok=True)  # Create directories if they don't exist

    # Save MIDI file in the "Midi" folder
    midi_path = os.path.join(midi_folder, midi_file_name)
    midi.save(midi_path)
    print(f"MIDI file saved at: {midi_path}")


def clean_up_midi(midi_file):
    midi_helper = MidiFile(midi_file)
    midi_result = MidiFile()
    midi_result.tracks.append(MidiTrack())
    for i, track in enumerate(midi_helper.tracks):
        # Iterate through messages in the track
        for msg in track:
            if hasattr(msg, "time") and msg.type == "note_off":
                if msg.time < 5:
                    pass


def main_analysis(file_path, midi_file_name, time_step=0.015625, lower_limit="C0", upper_limit="C8"):
    # pitch_values, timestamps, a, s = analyze_crepe(file_path, time_step)
    pitch_values, timestamps = analyze_parselmouth(file_path, time_step)

    plot_melody(timestamps, pitch_values)
    create_midi_file(timestamps, pitch_values, lower_limit, upper_limit, midi_file_name)


# Example usage
# file_path = "MusicFiles/Audio/Dream Theater - The Best Of Times Isolated Guitar Solo (John Petrucci).mp3"
file_path = "MusicFiles/Audio/FCtest.wav"
midi_file_name = "output_fc_pm.mid"


# # files
# src = "MusicFiles/Audio/Dream Theater - The Best Of Times Isolated Guitar Solo (John Petrucci).mp3"
# dst = "DT-The-Best-Of-Times-Solo.wav"
#
# # convert wav to mp3
# sound = AudioSegment.from_mp3(src)
# sound.export(dst, format="wav")

# main_analysis(file_path, midi_file_name, 0.01)
# mp3_to_wav("MusicFiles/Audio/FCtest.mp3", "FCtest.wav")

# print(clean_up_sliding_wnd([1, 3, 5, 7, 6,  4, 2], 5))

# Function to print MIDI file info
def print_midi_info(midi_file_path):
    # Load the MIDI file
    midi = MidiFile(midi_file_path)

    # Print general file information
    print(f"File: {midi_file_path}")
    print(f"Type: {midi.type}")
    print(f"Number of tracks: {len(midi.tracks)}")
    print(f"Ticks per beat (PPQ): {midi.ticks_per_beat}")
    print("\n--- Track Details ---\n")

    # Iterate through tracks
    for i, track in enumerate(midi.tracks):
        print(f"Track {i}: {track.name}")
        print(f"Number of messages: {len(track)}")

        # Iterate through messages in the track
        for msg in track:
            print(msg)
        print("\n" + "-" * 30 + "\n")


# Min heap of melodies by difference

# notes = PresentNotes("Temp2.mid")
# print(notes)
#
#
# for i in range(0, len(Temps[6].tracks[0])):
#     if hasattr(Temps[6].tracks[0][i], "note"):
#         print(Temps[6].tracks[0][i].note, Temps[6].tracks[0][i].type, Temps[6].tracks[0][i].time, end=" -> ")


# Temps = []
# for i in range(7):
#     Temps.append(MidiFile(f"Temp{i+1}.mid", clip=True))
#
# print(Temps[1].tracks[0])

# print(CompareSequences("Temp2.mid", "Temp1.mid"))


# for i in range(1, len(Temps[1].tracks[0])):
#     if hasattr(Temps[1].tracks[0][i], "type") and Temps[1].tracks[0][i].type == 'note_on' \
#             and Temps[1].tracks[0][i-1].type == "note_off" and Temps[1].tracks[0][i-1].time != 0:
#         Temps[1].tracks[0][i].time = 0
#
# print(Temps[1].tracks[0][:10])
#
#
# Temps[1].save("new_song.mid")
