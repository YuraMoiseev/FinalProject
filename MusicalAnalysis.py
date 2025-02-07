import librosa
import numpy as np
import matplotlib.pyplot as plt
import parselmouth
from mido import MetaMessage, Message, MidiFile, MidiTrack, bpm2tempo
import os
import crepe
from scipy.io import wavfile
# from pydub import AudioSegment
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

TIMING_CONST = 24
TIMING_WEIGHT = 0.001
MELODY_WEIGHT = 1 - TIMING_WEIGHT


class MidiAnalyzer:

    def __init__(self, midi):
        self.midi = midi
        self.check_validity()
        self.note_sequence = self.note_sequences()
        self.timing_sequence = self.timing_sequences()


    @classmethod
    def load_file(cls, file_name):
        # Preprocess inputs and call __init__
        return cls(MidiFile(file_name, clip=True))


    def check_validity(self):
        for track in self.midi.tracks:
            active_notes = {}
            for instance in track:
                if hasattr(instance, "note"):
                    if instance.type == "note_off":
                        if instance.note not in active_notes:
                            raise Exception("Exception on creating MidiAnalyzer - Invalid midi object")
                        active_notes.pop(instance.note)
                    else:
                        if instance.note in active_notes:
                            raise Exception("Exception on creating MidiAnalyzer - Invalid midi object")
                        active_notes[instance.note] = None



    def note_sequences(self):
        try:
            tracks = []
            for track in self.midi.tracks:
                track_notes = []
                active_notes = {}
                for instance in track:
                    if hasattr(instance, "note"):
                        if instance.type == "note_on":
                            if len(active_notes) == 0 and instance.time > 0:
                                track_notes.append(-1)
                            track_notes.append(instance.note)
                            active_notes[instance.note] = None
                        if instance.type == "note_off":
                            active_notes.pop(instance.note)
                tracks.append(track_notes)
            return tracks
        except Exception as e:
            print(f"Exception on extracting note sequences: {e}")


    def timing_sequences(self):
        try:
            tracks = []
            for track in self.midi.tracks:
                track_timings = []
                active_notes = {}
                for instance in track:
                    if hasattr(instance, "time"):
                        active_notes = {note: time + instance.time for note, time in active_notes.items()}
                        if instance.type == "note_on":
                            if len(active_notes) == 0 and instance.time > 0:
                                track_timings.append(instance.time)
                            active_notes[instance.note] = 0
                        if instance.type == "note_off":
                            track_timings.append(active_notes[instance.note])
                            active_notes.pop(instance.note)
                tracks.append(track_timings)
            return tracks
        except Exception as e:
            print(f"Exception on extracting timing sequences: {e}")


    # Function to map frequencies to the nearest note
    @staticmethod
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
    @staticmethod
    def restrict_to_range(note):
        if note is None:
            return None
        note_name, octave = note[:-1], int(note[-1])
        target_octave = octave % 8
        return f"{note_name}{target_octave}"


    def paired_sequences_song(self):
        return [self.paired_sequences_track(i) for i in range(len(self.midi.tracks))]

    def paired_sequences_track(self, i=0):
        return [[note] for note in self.note_sequence[i]], [[time] for time in self.timing_sequence[i]]

    # receives instances of series of notes and relative times and finds the most similar parts
    @staticmethod
    def _closest_sequences_2(track1, track2):
        sliding_window_length = len(track1[0])
        res = -1, -1
        for i in range(len(track2[0]) - sliding_window_length + 1):
            notes = (track1[0], track2[0][i:i + sliding_window_length])
            timings = (track1[1], track2[1][i:i + sliding_window_length])

            # print(notes)
            # print()
            # print(timings)
            # print("\n")

            melody_dtw = fastdtw(track1[0], notes[1], dist=euclidean)
            timings_dtw = fastdtw(track1[1], timings[1], dist=euclidean)

            similarity = melody_dtw[0] * MELODY_WEIGHT + timings_dtw[0] * TIMING_WEIGHT

            if similarity < res[0] or res[1] == -1:
                res = similarity, i

        return res

    def compare_midis(self, midi_object):
        result = -1, -1, -1
        user_sequences = self.paired_sequences_song()
        song_sequences = midi_object.paired_sequences_song()
        for i in range(len(song_sequences)):
            for j in range(len(user_sequences)):
                track_result = self._closest_sequences_2(user_sequences[j], song_sequences[i])
                if (track_result[0] < result[0] and track_result[0]!=-1) or result[0] == -1:
                    result = track_result[0], (i, j)
        return result

    @classmethod
    def compare_songs(cls, user_file, song_file):
        song_sequences = MidiAnalyzer.load_file(song_file)
        user_sequences = MidiAnalyzer.load_file(user_file)
        return user_sequences.compare_midis(song_sequences)

    @staticmethod
    def similarity(distance: float):
        return 100 / (1 + distance / 10000)


class AudioAnalyzer:

    def __init__(self, file_path):

        self.file_path = file_path
        self.midi_object = MidiFile()

    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Convert note limits to frequencies
    note_to_freq = {
        'C0': 16.35, 'C1': 32.7, 'C2': 65.41, 'C3': 130.81, 'C4': 261.63, 'C5': 523.25, 'C6': 1046.50, 'C7': 2093,
        'C8': 4186.01
    }

    @classmethod
    def _note_names(cls):
        return cls.note_names

    @classmethod
    def _note_frequencies(cls):
        return cls.note_to_freq

    @staticmethod
    # Function to map frequencies to the nearest note
    def frequency_to_note_name(frequency):
        if frequency <= 0:
            return None
        A4 = 440.0
        C0 = A4 * pow(2, -4.75)
        h = round(12 * np.log2(frequency / C0))
        octave = h // 12
        n = h % 12
        return f"{AudioAnalyzer._note_names()[n]}{octave}"

    @staticmethod
    # Restrict note to a specific octave range (e.g., C3 to C4)
    def restrict_to_range(note):
        if note is None:
            return None
        note_name, octave = note[:-1], int(note[-1])
        target_octave = octave % 8
        return f"{note_name}{target_octave}"


    def analyze_parselmouth(self, time_step, keep_stamps=True):
        # Parse the sound file
        sound = parselmouth.Sound(self.file_path)
        pitch = sound.to_pitch(time_step=time_step)

        # Get pitch values and timestamps
        pitch_values = pitch.selected_array['frequency']
        timestamps = np.arange(len(pitch_values)) * pitch.time_step

        if keep_stamps:
            self.update_midi_file(timestamps, pitch_values, "C0", "C8")

        return pitch_values, timestamps


    def analyze_librosa(self, time_step, keep_stamps=True):
        # Load the audio file
        y, sr = librosa.load(self.file_path, sr=None)  # sr=None preserves the original sample rate

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

        if keep_stamps:
            self.update_midi_file(timestamps, pitch_values, "C0", "C8")

        return pitch_values, timestamps


    def analyze_crepe(self, time_step, keep_stamps=True):

        """
            Analyze the pitch of the audio file using CREPE.

            Parameters:
                time_step (float): Time step in seconds for pitch analysis.
                keep_stamps (bool): Whether to keep pitch values and timestamps lists in the memory of the object

            Returns:
                1) In case of mono audio: returns two lists, the first one containing pitch values at all given points in time, the second one containing matching timestamps, also return two None instances as placeholders
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
        sample_rate, audio = wavfile.read(self.file_path)

        # Check if the audio is mono or stereo, in the first case - analyze right away
        if len(audio.shape) != 2 or audio.shape[1] != 2:
            timestamps, frequencies = process_channel(audio)
            if keep_stamps:
                self.update_midi_file(timestamps, frequencies, "C0", "C8")

            return process_channel(audio)[1], process_channel(audio)[0], None, None

        # Separate the left and right channels
        left_channel = audio[:, 0]
        right_channel = audio[:, 1]

        # Analyze both channels
        left_timestamps, left_frequencies = process_channel(left_channel)
        right_timestamps, right_frequencies = process_channel(right_channel)

        if keep_stamps:
            self.update_midi_file(right_timestamps, right_frequencies, "C0", "C8")
            self.update_midi_file(left_timestamps, left_frequencies, "C0", "C8")

        return right_frequencies, right_timestamps, left_frequencies, left_timestamps


    def update_midi_file(self, timestamps, pitch_values, lower_limit, upper_limit, track_name=None):

        lower_freq = AudioAnalyzer._note_frequencies()[lower_limit]
        upper_freq = AudioAnalyzer._note_frequencies()[upper_limit]

        # Add a track with a name to the MIDI file
        track = MidiTrack()
        if track_name is None:
            track.append(MetaMessage('track_name', name=f"track{len(self.midi_object.tracks)}"))
        else:
            track.append(MetaMessage('track_name', name=track_name))

        self.midi_object.tracks.append(track)

        # Add MIDI events
        ppq = 500  # Pulses per quarter note
        last_time = 0
        last_note = None

        delta_time = 0
        last_true_note = None # The last note which is in the restricted range and is not silent

        for t, freq in zip(timestamps, pitch_values):
            # Handle silent or out-of-limits notes
            if freq == 0 or not (lower_freq <= freq <= upper_freq):
                restricted_note = None
                midi_note = None
            else:
                note_name = self.frequency_to_note_name(freq)
                restricted_note = self.restrict_to_range(note_name)

                # Convert note name to MIDI note number
                midi_note = AudioAnalyzer._note_names().index(restricted_note[:-1]) + (int(restricted_note[-1]) + 1) * 12

            if restricted_note != last_note:
                # The current note is not silent and the previous also was not, open the current note and close the previous note
                if last_note is not None and restricted_note is not None:
                    midi_last_note = AudioAnalyzer._note_names().index(last_note[:-1]) + (int(last_note[-1]) + 1) * 12
                    track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))
                    delta_time = 0
                    track.append(Message('note_on', note=midi_note, velocity=64, time=round(delta_time)))
                    last_true_note = restricted_note

                # The current note is silent and the previous was not, close the previous note
                if last_note is not None and restricted_note is None:
                    midi_last_note = AudioAnalyzer._note_names().index(last_note[:-1]) + (int(last_note[-1]) + 1) * 12
                    track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))
                    delta_time = 0

                # If the previous note was silent and current isn't, open the current note
                if last_note is None and restricted_note is not None:
                    track.append(Message('note_on', note=midi_note, velocity=64, time=round(delta_time)))
                    delta_time = 0
                last_note = restricted_note

            # Calculate delta time
            delta_time += (t - last_time) * ppq / (1 / 2)  # Assuming 1/2 seconds per beat for 120 BPM
            last_time = t

        # Close the last note
        if last_note is not None and last_true_note is not None:
            midi_last_note = AudioAnalyzer._note_names().index(last_true_note[:-1]) + (int(last_true_note[-1]) + 1) * 12
            track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))

        return self.midi_object


    def save_midi(self, midi_file_name):

        project_folder = os.getcwd()  # Get the project folder path
        midi_folder = os.path.join(project_folder, "MusicFiles", "Midi")
        os.makedirs(midi_folder, exist_ok=True)  # Create directories if they don't exist

        # Save MIDI file in the "Midi" folder
        midi_path = os.path.join(midi_folder, midi_file_name)
        self.midi_object.save(midi_path)


#-----------------------------

#-----------------------------


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
                    res1.append(j.time)
                    time = 0
        res.append(res1)
    return res


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


def main_analysis(file_path, midi_file_name, time_step=0.015625, lower_limit="C0", upper_limit="C8"):
    # pitch_values, timestamps, _, _ = analyze_crepe(file_path, time_step)
    pitch_values, timestamps = analyze_parselmouth(file_path, time_step)

    plot_melody(timestamps, pitch_values)
    create_midi_file(timestamps, pitch_values, lower_limit, upper_limit, midi_file_name)


def separate_into_tracks(file_name):
    # Get the file type
    file_type = file_name.split(".")[-1]
    # Command to run Demucs
    command = f"demucs --{file_type} {file_name}"

    # Execute the command
    os.system(command)


def paired_sequences_song(file):
    return [paired_sequences_melody(file, i) for i in range(len(MidiFile(file).tracks))]


def paired_sequences_melody(file, i=0):
    return [[note] for note in note_sequences(file)[i]], [[time] for time in timing_sequences(file)[i]]


# receives instances of series of notes and relative times and finds the most similar parts
def closest_sequences_2(user_sample, track):
    sliding_window_length = len(user_sample[0])
    res = -1, -1
    for i in range(len(track[0]) - sliding_window_length + 1):
        notes = (user_sample[0], track[0][i:i + sliding_window_length])
        timings = (user_sample[1], track[1][i:i + sliding_window_length])

        # print(notes)
        # print()
        # print(timings)
        # print("\n")

        melody_dtw = fastdtw(notes[0], notes[1], dist=euclidean)
        timings_dtw = fastdtw(timings[0], timings[1], dist=euclidean)

        similarity = melody_dtw[0] * MELODY_WEIGHT + timings_dtw[0] * TIMING_WEIGHT

        if similarity < res[0] or res[1] == -1:
            res = similarity, i
    return res


def compare_melodies_2(user_file, song_file):
    user_sequence, song_sequence = paired_sequences_melody(user_file), paired_sequences_song(song_file)
    result = -1, -1, -1
    for i in range(len(song_sequence)):
        track_result = closest_sequences_2(user_sequence, song_sequence[i])
        if track_result[0] > result[0] or result[0] == -1:
            result = track_result[0], (i, track_result[1])
    return result


def similarity(distance: float):
    return 100 / (1 + distance/1000)


file_name = 'MusicFiles/Audio/MidiTestPiano.wav'
midi_file = 'MidiTestPianoDetected1.mid'

midi1 = "MusicFiles/Midi/MidiTestPianoDetected1.mid"
midi2 = "MusicFiles/Midi/MidiTestPiano2.mid"

# AA = AudioAnalyzer(file_name)
# AA.analyze_crepe(0.01)
# AA.analyze_librosa(0.01)
# AA.analyze_parselmouth(0.01)
# AA.save_midi(midi_file)

MA = MidiAnalyzer.load_file(midi1)
val = MA.compare_midis(MidiAnalyzer.load_file(midi2))
# val = MA.compare_midis(MA)

print(val)
print(str(MidiAnalyzer.similarity(val[0])) + "%")
# best_distance, best_position = compare_melodies_2(midi2, midi1)
# print(f"Best match found at position {best_position} with similarity {similarity(best_distance)}%")



