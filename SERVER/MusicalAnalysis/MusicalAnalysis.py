# Libraries
import librosa
import parselmouth
from mido import MetaMessage, Message, MidiFile, MidiTrack, bpm2tempo
import crepe
from scipy.io import wavfile
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import io
import heapq
import torch
import torchcrepe
import os
import uuid
import yt_dlp
import torchaudio
from demucs.pretrained import get_model
from demucs.apply import apply_model
import numpy as np
from pytube import YouTube
import re
from pydub import AudioSegment
import math

# Local
from SERVER.config_utils.config import WASC
from SERVER.config_utils.utils import write_to_log
from rust_code import MidiDTW, MIDITrack


def get_complete_file_path(file_type, file_name, dir):
    project_folder = os.getcwd()  # Get the project folder path
    os.makedirs(dir, exist_ok=True)  # Ensure the directory exists
    unique_id = uuid.uuid4().hex  # Generate a unique identifier
    file_path = os.path.join(project_folder, dir, f"{file_name}_{unique_id}.{file_type}")
    return file_path


def validate_url(url):
    """
    Validates if the URL is a valid YouTube link and checks if the video exists.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is a valid YouTube link and the video exists, False otherwise.
    """
    # Check if the URL is a valid YouTube URL
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )

    match = re.match(youtube_regex, url)
    if not match:
        return False  # Not a valid YouTube URL

    # Extract the video ID
    video_id = match.group(6)

    # Check if the video exists using pytube
    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        yt.check_availability()  # Raises an exception if the video is unavailable
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def to_wav(file_name):
    sound = AudioSegment.from_mp3(file_name)
    new_file = file_name[:file_name.find(".")] + ".wav"
    sound.export(new_file, format="wav")
    return new_file


class AudioExtractor:
    def __init__(self, format="wav"):
        self.format = format
        self.opts = {
        'format': 'bestaudio/best',  # Download the best quality audio
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Use FFmpeg to extract audio
            'preferredcodec': self.format,      # Convert to WAV format
            'preferredquality': '192',    # Set the audio quality
        }],
        'outtmpl': "",       # Output file name (without extension)
        }
        self.ydl = None

    def download_audio(self, url):
        print("Downloading audio from YouTube...")
        try:
            # Generate the output file path
            output_path = get_complete_file_path(self.format, "Audio", "../ServerFiles")

            self.opts['outtmpl'] = output_path[:-4]

            self.ydl = yt_dlp.YoutubeDL(self.opts)

            self.ydl.download([url])

            print(f"Audio downloaded successfully to {output_path}")
            return output_path

        except Exception as e:
            print(f"Failed to download audio: {e}")
            return None


class MidiAnalyzer:

    def __init__(self, midi, resolutions):
        self.midi = midi
        self.check_validity()
        self.note_sequence = self.note_sequences()
        self.timing_sequence = self.timing_sequences()
        self.progression_sequence = self.progression_sequences()
        self.resolutions = resolutions

    @classmethod
    def load_file(cls, file_name):
        # Preprocess inputs and call __init__
        return cls(MidiFile(file_name, clip=True))


    @classmethod
    def load_from_audio_analyzer(cls, AA_object):
        return cls(AA_object.midi_object, AA_object.resolutions)


    def check_validity(self):
        for track in self.midi.tracks:
            active_notes = {}
            for instance in track:
                if hasattr(instance, "note"):
                    if instance.type == "note_off":
                        if instance.note not in active_notes:
                            print(self.midi)
                            raise Exception("Exception on creating MidiAnalyzer - Invalid midi object (note_off event on non-existing note)")
                        active_notes.pop(instance.note)
                    else:
                        if instance.note in active_notes:
                            print(self.midi)
                            raise Exception("Exception on creating MidiAnalyzer - Invalid midi object (note_on event on active note)")
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
            tempo = 120 # default tempo
            for track in self.midi.tracks:
                track_timings = []
                active_notes = {}
                for instance in track:
                    sec_time = instance.time * 60000 / (self.midi.ticks_per_beat * tempo)
                    if instance.type == "set_tempo": # handle tempo change
                        tempo = instance.tempo
                    if hasattr(instance, "time"):
                        active_notes = {note: time + sec_time for note, time in active_notes.items()}
                        if instance.type == "note_on":
                            if len(active_notes) == 0 and sec_time > 0:
                                track_timings.append(sec_time)
                            active_notes[instance.note] = 0
                        if instance.type == "note_off":
                            track_timings.append(active_notes[instance.note])
                            active_notes.pop(instance.note)
                tracks.append(track_timings)
            return tracks
        except Exception as e:
            print(f"Exception on extracting timing sequences: {e}")


    def progression_sequences(self):
        try:
            tracks = []
            for sequence in self.note_sequence:
                track = []
                last_note = None
                for note in sequence:
                    if note == -1:
                        track.append(0)
                    if last_note is None:
                        last_note = note
                    elif last_note < note:
                        track.append(1)
                        last_note = note
                    elif last_note > note:
                        track.append(-1)
                        last_note = note
                    else:
                        track.append(0)
                tracks.append(track)
            return tracks
        except Exception as e:
            print(f"Exception on extracting progression sequences: {e}")

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
        return [[note] for note in self.note_sequence[i]], [[time] for time in self.timing_sequence[i]], [[prog] for prog in self.progression_sequence[i]]

    @staticmethod
    def weigh_distance(dist, consts):
        try:
            weighted_dist = consts["a"] ** (1 + (dist - consts["x0"]) / consts["s"])
            first_correcting_factor = 1 / (1 + consts["b"] ** ((consts["x0"] - dist) / consts["s"]))
            second_correcting_factor = 2 / (1 + math.e ** (2 * (-dist))) - 1
            third_correcting_factor = 2 * consts["y0"] * (1 + math.e ** (2 * (-consts["x0"]))) / (1 - math.e ** (2 * (-consts["x0"])))

            return weighted_dist * first_correcting_factor * second_correcting_factor * third_correcting_factor
        except Exception:
            return math.inf


    def weigh_distances(self, progression_d, note_d, timing_d):
        weighted_progs = self.weigh_distance(progression_d, WASC["d"])
        weighted_notes = self.weigh_distance(note_d, WASC["n"])
        weighted_timings = self.weigh_distance(timing_d, WASC["t"])
        return weighted_progs, weighted_notes, weighted_timings


    # receives instances of series of notes and relative times and finds the most similar parts
    def _closest_sequences_2(self, track1, track2):
        sliding_window_length = len(track1[0])
        res = -1, -1 # set base values

        if sliding_window_length >= len(track2[0]):
            notes = (track1[0], track2[0])
            timings = (track1[1], track2[1])
            progressions = (track1[2], track2[2])
            # skip empty melodies
            if any([len(lst)==0 for lst in [notes[0], notes[1], timings[0], timings[1], progressions[0], progressions[1]]]):
                return res

            melody_dtw = fastdtw(notes[0], notes[1], dist=euclidean)
            timings_dtw = fastdtw(timings[0], timings[1], dist=euclidean)
            progressions_dtw = fastdtw(progressions[0], progressions[1], dist=euclidean)

            p, m, t = self.weigh_distances(progressions_dtw[0], melody_dtw[0], timings_dtw[0])

            weighted_distance = p * WASC["d"]["w"] + m * WASC["n"]["w"] + t * WASC["t"]["w"]

            res = weighted_distance, 0 # return the distance at the time 0

        else:
            iterations = len(track2[0]) - sliding_window_length + 1 # the amount of checks
            last_printed = 0
            for i in range(0, iterations):  #, max(1, iterations//200)):    
                percent = (i+1)*100//iterations    
                if  percent % 10 == 0 and percent > last_printed:
                    write_to_log(f"Done {percent}%...")
                    last_printed = percent
                notes = (track1[0], track2[0][i:i + sliding_window_length])
                timings = (track1[1], track2[1][i:i + sliding_window_length])
                progressions = (track1[2], track2[2][i:i + sliding_window_length-1])
                # skip empty melodies
                if any([len(lst)==0 for lst in [notes[0], notes[1], timings[0], timings[1], progressions[0], progressions[1]]]):
                    continue

                # print(notes)
                # print()
                # print(timings)
                # print("\n")

                melody_dtw = fastdtw(notes[0], notes[1], dist=euclidean)[0] / sliding_window_length
                timings_dtw = fastdtw(timings[0], timings[1], dist=euclidean)[0] / sliding_window_length
                progressions_dtw = fastdtw(progressions[0], progressions[1], dist=euclidean)[0] / sliding_window_length

                p, m, t = self.weigh_distances(progressions_dtw, melody_dtw, timings_dtw)

                weighted_distance = (p * WASC["d"]["w"] + m * WASC["n"]["w"] + t * WASC["t"]["w"]) / (WASC["d"]["w"] + WASC["n"]["w"] + WASC["t"]["w"])
                if weighted_distance < res[0] or res[1] == -1:
                    res = weighted_distance, self._convert_id_to_time(i, track2[1]) # sum up all the times to get a relative time from the beginning of the track
                    print("MELODY_DTW: " + str(m) + "   TIMING_DTW: " + str(t) + "   PROG_DTW: " + str(p) + "   AT TIME: " + str(res[1]))



        return res

    @staticmethod
    def _convert_id_to_time(i, timing_sequence):
        return sum([sum(time_vector) for time_vector in timing_sequence[:i]])

    # TODO: only check adjacent tracks!
    def compare_midis(self, midi_object):
        result_distance = -1, -1, -1
        user_sequences = self.paired_sequences_song()
        song_sequences = midi_object.paired_sequences_song()
        for i in range(len(song_sequences)):
            for j in range(len(user_sequences)):
                track_result = self._closest_sequences_2(user_sequences[j], song_sequences[i])
                if (track_result[0] < result_distance[0] or result_distance[0] == -1) and track_result[0]!=-1:
                    result_distance = track_result[0], (i, j), track_result[1]
        return result_distance

    @classmethod
    def compare_songs(cls, user_file, song_file):
        song_sequences = MidiAnalyzer.load_file(song_file)
        user_sequences = MidiAnalyzer.load_file(user_file)
        return user_sequences.compare_midis(song_sequences)
    
    def paired_sequences_song_rust(self):
        return [self.paired_sequences_track_rust(i) for i in range(len(self.midi.tracks))]

    def paired_sequences_track_rust(self, i=0):
        return MIDITrack(self.note_sequence[i], self.timing_sequence[i], self.progression_sequence[i], self.resolutions)
    
    def compare_midis_rust(self, midi_object):
        user_sequences = self.paired_sequences_song_rust()
        song_sequences = midi_object.paired_sequences_song_rust()
        comparator = MidiDTW()
        return comparator.compare_midis(user_sequences, song_sequences)


    # Calculate similarity in percents
    @staticmethod
    def similarity(weighed_distance: float):
        if weighed_distance == -1:
            return 0
        return 100 / (1 + weighed_distance)

    @classmethod
    def load_midi_from_blob(cls, blob_data, resolutions):
        file_data = io.BytesIO(blob_data)
        return cls(MidiFile(file=file_data, clip=True), resolutions=resolutions)

    def compare_to_db(self, song_dict):
        top_matches = []
        # print(song_dict)
        for (name, artist), midi_blob in song_dict.items():
            midi_object = MidiAnalyzer.load_midi_from_blob(midi_blob)
            distance, track_indices, time = self.compare_midis(midi_object)
            print(f"DISTANCE: {distance}")
            similarity = MidiAnalyzer.similarity(distance)

            # Push only if we have fewer than 20 results or the new distance is better and the time is not -1
            if len(top_matches) < 20:
                heapq.heappush(top_matches, (similarity, name, artist, time, track_indices))
            else:
                heapq.heappushpop(top_matches, (similarity, name, artist, time, track_indices))

        # Sort results by best (biggest) similarity
        return sorted(top_matches, key=lambda x: x[0], reverse=True)
    

    def compare_to_db_rust(self, song_dict):
        top_matches = []
        # print(song_dict)
        for (name, artist, resolutions), midi_blob in song_dict.items():
            midi_object = MidiAnalyzer.load_midi_from_blob(midi_blob, resolutions)
            distance, track_indices, time = self.compare_midis_rust(midi_object)
            print(f"DISTANCE: {distance}")
            similarity = MidiAnalyzer.similarity(distance)

            # Push only if we have fewer than 20 results or the new distance is better and the time is not -1
            if len(top_matches) < 20:
                heapq.heappush(top_matches, (similarity, name, artist, time, track_indices))
            else:
                heapq.heappushpop(top_matches, (similarity, name, artist, time, track_indices))

        # Sort results by best (biggest) similarity
        return sorted(top_matches, key=lambda x: x[0], reverse=True)


class AudioAnalyzer:
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    NOTE_TO_FREQ = {
        'C0': 16.35, 'C1': 32.7, 'C2': 65.41, 'C3': 130.81, 'C4': 261.63,
        'C5': 523.25, 'C6': 1046.50, 'C7': 2093, 'C8': 4186.01
    }

    def __init__(self, file_path=None):
        self.file_path = file_path
        self.midi_object = MidiFile(ticks_per_beat=480)
        self.lists = []
        self.resolutions = []

    @staticmethod
    def frequency_to_note_name(frequency):
        if frequency <= 0:
            return None
        A4 = 440.0
        C0 = A4 * pow(2, -4.75)
        h = round(12 * np.log2(frequency / C0))
        octave = h // 12
        n = h % 12
        return f"{AudioAnalyzer.NOTE_NAMES[n]}{octave}"

    @staticmethod
    def restrict_to_range(note):
        if note is None:
            return None
        note_name, octave = note[:-1], int(note[-1])
        target_octave = octave % 8
        return f"{note_name}{target_octave}"

    def analyze_librosa(self, time_step, keep_stamps=True, track_name=""):
        y, sr = librosa.load(self.file_path, sr=None)
        hop_length = int(time_step * sr)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
        pitch_values = [pitches[:, i][magnitudes[:, i].argmax()] for i in range(pitches.shape[1]) if
                        magnitudes[:, i].any()]
        timestamps = np.arange(len(pitch_values)) * time_step
        if keep_stamps:
            self.update_midi_file(timestamps, pitch_values, "C0", "C8", track_name+"librosa")
            self.resolutions = time_step
        return pitch_values, timestamps

    def analyze_torchcrepe(self, time_step, keep_stamps=True, track_name=""):
        try:
            audio_path = self.file_path
            # Load and preprocess audio
            audio, sr = librosa.load(audio_path, sr=16000)

            if torch.cuda.is_available():
                audio = torch.tensor(audio).unsqueeze(0).to("cuda")  # Move to GPU if available
            else:
                audio = torch.tensor(audio).unsqueeze(0)

            # Compute hop length
            hop_length = int(time_step * sr)

            # Run pitch prediction
            result = torchcrepe.predict(audio, sr, hop_length=hop_length, fmin=50, fmax=2000, model='full')

            # Handle return value
            if isinstance(result, tuple):
                pitches, _ = result
            else:
                pitches = result

            # Convert tensor to a list of pitches
            pitches_list = pitches.squeeze().tolist()  # Remove batch dimension and convert to list

            # Generate timestamps
            timestamps = torch.arange(len(pitches_list)) * (hop_length / sr)
            timestamps_list = timestamps.tolist()  # Convert timestamps to list

            if keep_stamps:
                self.update_midi_file(timestamps_list, pitches_list, "C0", "C8", track_name+"torchcrepe")
                self.resolutions = time_step
        except Exception as e:
            write_to_log(f"Exception in analyze_torch_crepe: {str(e)}")

    def analyze_crepe(self, time_step, keep_stamps=True, track_name=""):
        def process_channel(channel_data):
            time, frequency, confidence, _ = crepe.predict(channel_data, sample_rate, step_size=int(time_step * 1000))
            valid_indices = confidence >= 0.5
            return time[valid_indices], frequency[valid_indices]

        sample_rate, audio = wavfile.read(self.file_path)
        if len(audio.shape) != 2 or audio.shape[1] != 2:
            timestamps, frequencies = process_channel(audio)
            if keep_stamps:
                self.update_midi_file(timestamps, frequencies, "C0", "C8")
                self.resolutions = time_step 
            return frequencies, timestamps, None, None
        left_timestamps, left_frequencies = process_channel(audio[:, 0])
        right_timestamps, right_frequencies = process_channel(audio[:, 1])
        if keep_stamps:
            self.update_midi_file(right_timestamps, right_frequencies, "C0", "C8", track_name+"crepe")
            self.update_midi_file(left_timestamps, left_frequencies, "C0", "C8", track_name+"crepe")
            self.resolutions = time_step 
        return right_frequencies, right_timestamps, left_frequencies, left_timestamps

    def analyze_full(self, time_step=0.05, keep_stamps=True, track_name=""):
        try:
            self.analyze_crepe(time_step, keep_stamps, track_name)
            self.analyze_librosa(time_step, keep_stamps, track_name)
            self.analyze_torchcrepe(time_step, keep_stamps, track_name)
        except Exception as e:
            write_to_log("Exception " + str(e))
            return

    def update_midi_file(self, timestamps, pitch_values, lower_limit, upper_limit, track_name=None, tempo=120):

        lower_freq = AudioAnalyzer.NOTE_TO_FREQ[lower_limit]
        upper_freq = AudioAnalyzer.NOTE_TO_FREQ[upper_limit]

        # Add a track with a name to the MIDI file
        track = MidiTrack()
        if track_name is None:
            track.append(MetaMessage('track_name', name=f"track{len(self.midi_object.tracks)}", ))
        else:
            track.append(MetaMessage('track_name', name=track_name + f'{len(self.midi_object.tracks)}'))

        track.append(MetaMessage("set_tempo", tempo=bpm2tempo(tempo)))

        self.midi_object.tracks.append(track)

        # Add MIDI events
        last_time = 0
        last_note = None

        delta_time = 0
        last_true_note = None  # The last note which is in the restricted range and is not silent

        for t, freq in zip(timestamps, pitch_values):
            # Handle silent or out-of-limits notes
            if freq == 0 or not (lower_freq <= freq <= upper_freq):
                restricted_note = None
                midi_note = None
            else:
                note_name = self.frequency_to_note_name(freq)
                restricted_note = self.restrict_to_range(note_name)

                # Convert note name to MIDI note number
                midi_note = AudioAnalyzer.NOTE_NAMES.index(restricted_note[:-1]) + (
                            int(restricted_note[-1]) + 1) * 12

            if restricted_note != last_note:
                # The current note is not silent and the previous also was not, open the current note and close the previous note
                if last_note is not None and restricted_note is not None:
                    midi_last_note = AudioAnalyzer.NOTE_NAMES.index(last_note[:-1]) + (int(last_note[-1]) + 1) * 12
                    track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))
                    delta_time = 0
                    track.append(Message('note_on', note=midi_note, velocity=64, time=round(delta_time)))
                    last_true_note = restricted_note

                # The current note is silent and the previous was not, close the previous note
                if last_note is not None and restricted_note is None:
                    midi_last_note = AudioAnalyzer.NOTE_NAMES.index(last_note[:-1]) + (int(last_note[-1]) + 1) * 12
                    track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))
                    delta_time = 0

                # If the previous note was silent and current isn't, open the current note
                if last_note is None and restricted_note is not None:
                    track.append(Message('note_on', note=midi_note, velocity=64, time=round(delta_time)))
                    delta_time = 0
                    last_true_note = restricted_note
                last_note = restricted_note

            # Calculate delta time
            delta_time += (t - last_time) * self.midi_object.ticks_per_beat * 2  # Assuming 2 beats per second for 120 BPM
            last_time = t

        # Close the last note
        if last_note is not None and last_true_note is not None:
            midi_last_note = AudioAnalyzer.NOTE_NAMES.index(last_true_note[:-1]) + (int(last_true_note[-1]) + 1) * 12
            track.append(Message('note_off', note=midi_last_note, velocity=64, time=round(delta_time)))

        return self.midi_object

    def save_midi(self, midi_file_name):
        midi_folder = os.path.join(os.getcwd(), "MusicFiles", "Midi")
        os.makedirs(midi_folder, exist_ok=True)
        midi_path = os.path.join(midi_folder, midi_file_name)
        self.midi_object.save(midi_path)
        return midi_path

    def change_base_file(self, file_path):
        self.file_path = file_path


class AudioSeparator:
    def __init__(self, file_path, base_dir="ServerFiles"):
        self.file_path = file_path
        self.base_dir = base_dir

        # Define directories
        self.demucs_dir = os.path.join(os.getcwd(), self.base_dir, "stems/demucs/")
        self.create_dirs()

    def create_dirs(self):
        """Creates necessary directories if they do not exist."""
        os.makedirs(self.demucs_dir, exist_ok=True)

    def change_base_file(self, file_path):
        """Change the base audio file for processing."""
        self.file_path = file_path

    def separate_demucs(self):
        """Separate stems using Hybrid Demucs and save them in the designated directory."""
        print("Running Hybrid Demucs...")

        model = get_model(name="htdemucs_6s")  # Hybrid Demucs model
        waveform, sample_rate = torchaudio.load(self.file_path)

        # Convert mono to stereo
        if waveform.shape[0] == 1:
            waveform = torch.cat([waveform, waveform], dim=0)

        # Apply model to extract sources
        sources = apply_model(model, waveform[None, ...])

        # Define stem mapping for Hybrid Demucs
        stem_indices = {
            "drums": 0,
            "bass": 1,
            "guitar": 2,
            "piano": 5,
            "vocals": 3,
            "other": 4
        }

        # Save each separated stem
        for stem, index in stem_indices.items():
            file_path = os.path.join(self.demucs_dir, f"{stem}.wav")
            torchaudio.save(file_path, sources.squeeze()[index], sample_rate)

        print(f"Hybrid Demucs stems saved in {self.demucs_dir}")

    def separate_all(self):
        """Run all separation steps."""
        try:
            self.separate_demucs()
            return self.demucs_dir
        except Exception as e:
            print(f"Error during separation: {e}")

#-----------------------------

#-----------------------------

# AA = AudioAnalyzer(file_name)
# AA.analyze_crepe(0.01)
# AA.analyze_librosa(0.01)
# AA.analyze_parselmouth(0.01)
# AA.save_midi(midi_file)
if __name__ == "__main__":
    file = "/SERVER/ServerFiles/Audio_ba4a7e78c4bc4aada61169f1c2a89995.wav"
    # file = "D:\Videos and Recordings\Audio\TWTIA\TWTIA.mp3"
    # AS = AudioSeparator(file_path = file, base_dir="D:\Videos and Recordings\Audio\TWTIA")
    # AS.separate_demucs()

    AA = AudioAnalyzer(file)
    AA.analyze_crepe(0.5, True)
    AA.analyze_librosa(0.5, True)
    MA1 = MidiAnalyzer.load_from_audio_analyzer(AA)

    AA2 = AudioAnalyzer(file)
    AA2.analyze_torchcrepe(file, 0.5, True)
    MA2 = MidiAnalyzer.load_from_audio_analyzer(AA2)
    import time
    start = time.time()
    a1 = MA2.compare_midis_rust(MA1)
    print("rust result:" + str(a1))
    print("rust runtime (with python api overhead):" + str(time.time()-start))
    start1 = time.time()
    a2 = MA2.compare_midis(MA1)
    print("python result:" + str(a2))
    print("python runtime:" + str(time.time()-start1))
    print("rust similarity:" + str(MA1.similarity(a1[0])) + "   python similarity:" + str(MA1.similarity(a2[0])))

    track1 = MIDITrack([1, 1, 3, 2, 5, 6], [0, 0.2, 0.3, 0.1, 0.5], [0, 1, -1, 1, 1])
    track2 = MIDITrack([0, 4, 2, 3, 11, 6], [0, 0.2, 0.3, 0.5, 0.1], [1, -1, 1, 1, -1])
    a1 = MidiDTW().compare_tracks(track1, track2)
    print("rust result:" + str(a1))

# best_distance, best_position = compare_melodies_2(midi2, midi1)
# print(f"Best match found at position {best_position} with similarity {similarity(best_distance)}%")



