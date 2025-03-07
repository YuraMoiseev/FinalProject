import librosa
import matplotlib.pyplot as plt
import parselmouth
from mido import MetaMessage, Message, MidiFile, MidiTrack, bpm2tempo
import os
import crepe
from scipy.io import wavfile
# from pydub import AudioSegment
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
from spleeter.separator import Separator
import openunmix
import soundfile as sf
import numpy as np
from pytube import YouTube
import re
from pydub import AudioSegment
from pydub.utils import make_chunks
from ConstantsAndLogging import write_to_log

coef = 10
TIMING_WEIGHT = 1
MELODY_WEIGHT = 100
PROGRESSION_WEIGHT = 1000
GENERAL_WEIGHT = TIMING_WEIGHT + MELODY_WEIGHT + PROGRESSION_WEIGHT


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
            output_path = get_complete_file_path(self.format, "Audio", "ServerFiles")

            self.opts['outtmpl'] = output_path[:-4]

            self.ydl = yt_dlp.YoutubeDL(self.opts)

            self.ydl.download([url])

            print(f"Audio downloaded successfully to {output_path}")
            return output_path

        except Exception as e:
            print(f"Failed to download audio: {e}")
            return None


class MidiAnalyzer:

    def __init__(self, midi):
        self.midi = midi
        self.check_validity()
        self.note_sequence = self.note_sequences()
        self.timing_sequence = self.timing_sequences()
        self.progression_sequence = self.progression_sequences()


    @classmethod
    def load_file(cls, file_name):
        # Preprocess inputs and call __init__
        return cls(MidiFile(file_name, clip=True))


    @classmethod
    def load_from_audio_analyzer(cls, AA_object):
        return cls(AA_object.midi_object)


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


    def progression_sequences(self):
        try:
            tracks = []
            for sequence in self.note_sequence:
                track = []
                last_note = None
                for note in sequence:
                    if note == -1:
                        continue
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

    # receives instances of series of notes and relative times and finds the most similar parts
    @staticmethod
    def _closest_sequences_2(track1, track2):
        sliding_window_length = len(track1[0])
        # if any(not lst for lst in track1) or any(not lst for lst in track2):
        #     return
        res = -1, -1
        for i in range(len(track2[0]) - sliding_window_length + 1):
            notes = (track1[0], track2[0][i:i + sliding_window_length])
            timings = (track1[1], track2[1][i:i + sliding_window_length])
            progressions = (track1[2], track2[2][i:i + sliding_window_length-1])

            # print(notes)
            # print()
            # print(timings)
            # print("\n")

            melody_dtw = fastdtw(notes[0], notes[1], dist=euclidean)
            timings_dtw = fastdtw(timings[0], timings[1], dist=euclidean)
            progressions_dtw = fastdtw(progressions[0], progressions[1], dist=euclidean)

            similarity = progressions_dtw[0] * PROGRESSION_WEIGHT + melody_dtw[0] * MELODY_WEIGHT + timings_dtw[0] * TIMING_WEIGHT

            if similarity < res[0] or res[1] == -1:
                res = similarity, i

        return res

    def compare_midis(self, midi_object):
        result_distance = -1, -1, -1
        user_sequences = self.paired_sequences_song()
        song_sequences = midi_object.paired_sequences_song()
        for i in range(len(song_sequences)):
            for j in range(len(user_sequences)):
                track_result = self._closest_sequences_2(user_sequences[j], song_sequences[i])
                if (track_result[0] < result_distance[0] and track_result[0]!=-1) or result_distance[0] == -1:
                    result_distance = track_result[0], (i, j)
        return result_distance

    @classmethod
    def compare_songs(cls, user_file, song_file):
        song_sequences = MidiAnalyzer.load_file(song_file)
        user_sequences = MidiAnalyzer.load_file(user_file)
        return user_sequences.compare_midis(song_sequences)

    @staticmethod
    def similarity(distance: float):
        return 100 / (1 + distance / (GENERAL_WEIGHT*10000))

    @classmethod
    def load_midi_from_blob(cls, blob_data):
        file_data = io.BytesIO(blob_data)
        return cls(MidiFile(file=file_data, clip=True))

    def compare_to_db(self, song_dict):
        top_matches = []

        for (name, artist), midi_blob in song_dict.items():
            midi_object = MidiAnalyzer.load_midi_from_blob(midi_blob)
            similarity = MidiAnalyzer.similarity(self.compare_midis(midi_object)[0])

            # Push only if we have fewer than 20 results or the new distance is better
            if len(top_matches) < 20:
                heapq.heappush(top_matches, (similarity, name, artist))
            else:
                heapq.heappushpop(top_matches, (similarity, name, artist))

        # Sort results by best (smallest) distance
        return sorted(top_matches, key=lambda x: x[0])


class AudioAnalyzer:
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    NOTE_TO_FREQ = {
        'C0': 16.35, 'C1': 32.7, 'C2': 65.41, 'C3': 130.81, 'C4': 261.63,
        'C5': 523.25, 'C6': 1046.50, 'C7': 2093, 'C8': 4186.01
    }

    def __init__(self, file_path):
        self.file_path = file_path
        self.midi_object = MidiFile()

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

    def analyze_parselmouth(self, time_step, keep_stamps=True):
        sound = parselmouth.Sound(self.file_path)
        pitch = sound.to_pitch(time_step=time_step)
        pitch_values = pitch.selected_array['frequency']
        timestamps = np.arange(len(pitch_values)) * pitch.time_step
        if keep_stamps:
            self.update_midi_file(timestamps, pitch_values, "C0", "C8")
        return pitch_values, timestamps

    def analyze_librosa(self, time_step, keep_stamps=True):
        y, sr = librosa.load(self.file_path, sr=None)
        hop_length = int(time_step * sr)
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, hop_length=hop_length)
        pitch_values = [pitches[:, i][magnitudes[:, i].argmax()] for i in range(pitches.shape[1]) if
                        magnitudes[:, i].any()]
        timestamps = np.arange(len(pitch_values)) * time_step
        if keep_stamps:
            self.update_midi_file(timestamps, pitch_values, "C0", "C8")
        return pitch_values, timestamps

    def analyze_crepe(self, time_step, keep_stamps=True):
        def process_channel(channel_data):
            time, frequency, confidence, _ = crepe.predict(channel_data, sample_rate, step_size=int(time_step * 1000))
            valid_indices = confidence >= 0.5
            return time[valid_indices], frequency[valid_indices]

        sample_rate, audio = wavfile.read(self.file_path)
        if len(audio.shape) != 2 or audio.shape[1] != 2:
            timestamps, frequencies = process_channel(audio)
            if keep_stamps:
                self.update_midi_file(timestamps, frequencies, "C0", "C8")
            return frequencies, timestamps, None, None
        left_timestamps, left_frequencies = process_channel(audio[:, 0])
        right_timestamps, right_frequencies = process_channel(audio[:, 1])
        if keep_stamps:
            self.update_midi_file(right_timestamps, right_frequencies, "C0", "C8")
            self.update_midi_file(left_timestamps, left_frequencies, "C0", "C8")
        return right_frequencies, right_timestamps, left_frequencies, left_timestamps

    def analyze_torchcrepe(self, audio_path, time_step, keep_stamps=True):
        audio, sr = librosa.load(audio_path, sr=16000)
        audio = torch.tensor(audio).unsqueeze(0)

        # Compute hop length based on time_step
        hop_length = int(time_step * sr)

        # Run pitch prediction
        pitches, _ = torchcrepe.predict(audio, sr, hop_length=hop_length, fmin=50, fmax=2000, model='full')

        # Generate timestamps
        timestamps = torch.arange(len(pitches)) * (hop_length / sr)

        if keep_stamps:
            self.update_midi_file(timestamps, pitches, "C0", "C8")

    def analyze_full(self, time_step=0.01, keep_stamps=True):
        try:
            self.analyze_crepe(time_step, keep_stamps)
            self.analyze_librosa(time_step, keep_stamps)
            self.analyze_parselmouth(time_step, keep_stamps)
            # self.analyze_torchcrepe(time_step, keep_stamps)
        except Exception as e:
            write_to_log("Exception" + str(e))

    def update_midi_file(self, timestamps, pitch_values, lower_limit, upper_limit, track_name=None):

        lower_freq = AudioAnalyzer.NOTE_NAMES[lower_limit]
        upper_freq = AudioAnalyzer.NOTE_TO_FREQ[upper_limit]

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
            delta_time += (t - last_time) * ppq / (1 / 2)  # Assuming 1/2 seconds per beat for 120 BPM
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

        # Define instance-specific directories
        self.demucs_dir = os.path.join(os.getcwd(), self.base_dir, "stems/demucs/")
        self.spleeter_dir = os.path.join(os.getcwd(), self.base_dir, "stems/spleeter/")
        self.openunmix_dir = os.path.join(os.getcwd(), self.base_dir, "stems/openunmix/")

        self.create_dirs()

    def create_dirs(self):
        """Creates necessary directories if they do not exist."""
        os.makedirs(self.demucs_dir, exist_ok=True)
        os.makedirs(self.spleeter_dir, exist_ok=True)
        os.makedirs(self.openunmix_dir, exist_ok=True)

    def change_base_file(self, file_path):
        """Change the base audio file for processing."""
        self.file_path = file_path

    def separate_demucs(self):
        """Separate stems using Demucs and save them in the designated directory."""
        print("Running Demucs...")

        # Load the pre-trained HTDemucs model
        model = get_model(name="htdemucs")

        # Load the input audio
        waveform, sample_rate = torchaudio.load(self.file_path)

        # Convert to stereo if it's mono
        if waveform.shape[0] == 1:
            waveform = torch.cat([waveform, waveform], dim=0)  # Duplicate mono to stereo

        # Perform separation
        sources = apply_model(model, waveform[None, ...])  # Add batch dimension

        # Map stems to their correct indices in the sources tensor
        stem_indices = {
            "vocals": 3,
            "drums": 0,
            "bass": 1,
            "other": 2
        }

        # Save the core stems
        for stem, index in stem_indices.items():
            file_path = os.path.join(self.demucs_dir, f"{stem}.wav")
            torchaudio.save(file_path, sources.squeeze()[index], sample_rate)

        print(f"Demucs stems saved in {self.demucs_dir}")

    @staticmethod
    def split_audio(input_audio, chunk_length_ms=1000): # 10 sec chunks by default
        """Split an audio file into smaller chunks."""
        audio = AudioSegment.from_file(input_audio)
        chunks = make_chunks(audio, chunk_length_ms)
        return chunks

    def separate_spleeter(self):
        """Separate additional stems using Spleeter (piano, synth, etc.) in batches."""
        print("Running Spleeter in batches...")

        # Path to "other" stem extracted by Demucs
        input_audio = os.path.join(self.demucs_dir, "other.wav")

        # Ensure the "other.wav" file exists
        if not os.path.exists(input_audio):
            print("Error: 'other.wav' from Demucs not found.")
            return

        # Initialize the Spleeter separator (4-stem mode)
        separator = Separator("spleeter:4stems")

        # Split the audio into chunks
        chunks = self.split_audio(input_audio)

        # Process each chunk
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i + 1}/{len(chunks)}...")

            # Save the chunk to a temporary file
            chunk_path = os.path.join(self.spleeter_dir, f"chunk_{i}.wav")
            chunk.export(chunk_path, format="wav")

            # Perform separation on the chunk
            temp_output = os.path.join(self.spleeter_dir, f"temp_spleeter_{i}/")
            os.makedirs(temp_output, exist_ok=True)
            separator.separate_to_file(chunk_path, temp_output)

            # Move extracted files to self.spleeter_dir
            for file in os.listdir(temp_output):
                if file.endswith(".wav"):
                    os.rename(
                        os.path.join(temp_output, file),
                        os.path.join(self.spleeter_dir, f"{file}_{i}.wav")
                    )

            # Clean up temporary files
            os.remove(chunk_path)
            os.rmdir(temp_output)

        print(f"Spleeter stems saved in {self.spleeter_dir}")

    def separate_openunmix(self):
        """Separate guitar and other instruments using Open-Unmix."""
        print("Running Open-Unmix...")

        # Path to "other" stem extracted by Demucs
        input_audio = os.path.join(self.demucs_dir, "other.wav")

        # Ensure the "other.wav" file exists
        if not os.path.exists(input_audio):
            print("Error: 'other.wav' from Demucs not found.")
            return

        # Load Open-Unmix model
        model = openunmix.predict.OpenUnmix(model_str="umxhq")

        # Load the "other" stem
        audio, rate = sf.read(input_audio)

        # Convert audio to tensor format
        audio_tensor = torch.tensor(audio.T, dtype=torch.float32)

        # Perform separation
        with torch.no_grad():
            estimates = model(audio_tensor[None, ...])  # Add batch dimension

        # Save the extracted guitar track
        guitar_path = os.path.join(self.openunmix_dir, "guitar.wav")
        sf.write(guitar_path, estimates[0].squeeze().numpy().T, rate)

        print(f"Guitar stem extracted successfully and saved to {guitar_path}")


    def separate_all(self):
        step = 1
        try:
            # self.separate_demucs()
            step = 2
            self.separate_spleeter()
            step = 3
            self.separate_openunmix()
        except Exception as e:
            write_to_log(f"Exception on step {step},\nfilepath {self.file_path},"
                         f" directories:\ndemucs: {self.demucs_dir}\nspleeter: {self.spleeter_dir}\nopenunmix: {self.openunmix_dir}\n"
                         f"Issue: {e}")


#-----------------------------

#-----------------------------

# AA = AudioAnalyzer(file_name)
# AA.analyze_crepe(0.01)
# AA.analyze_librosa(0.01)
# AA.analyze_parselmouth(0.01)
# AA.save_midi(midi_file)
if __name__ == "__main__":
    file = "C:/Users/Ymois/PycharmProjects/FinalProject/ServerFiles/Audio_ba4a7e78c4bc4aada61169f1c2a89995.wav"
    AS = AudioSeparator(file)
    AS.separate_all()
    print(file)

# best_distance, best_position = compare_melodies_2(midi2, midi1)
# print(f"Best match found at position {best_position} with similarity {similarity(best_distance)}%")



