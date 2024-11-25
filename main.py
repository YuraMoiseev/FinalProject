from mido import *
import editdistance
from sortedcontainers import SortedList

# currently just experimenting with comparing .mid files


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
TIMING_WEIGHT = 0.1
MELODY_WEIGHT = 1 - TIMING_WEIGHT


def PresentNotes(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        for j in i:
            if hasattr(j, "note") and j.note not in res:
                res.append(j.note)
    return res


def NoteSequences(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        res1 = []
        for j in i:
            if hasattr(j, "note") and j.type == "note_on":
                res1.append(j.note)
        res.append(res1)
    return res


def NoteSequences1(file):
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


def TimingSequences(file):
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


# takes all the tracks from 2 midi files and finds the most similar melody, gives the indexes of melodies and the staring point at which the most suitability was found
# MAIN FUNC FOR NOW!!!
def CompareMelodies(file1, file2, melody_length=-1):
    Melodies_1, Melodies_2 = (NoteSequences(file1), TimingSequences(file1)), (NoteSequences(file2), TimingSequences(file2))
    # set our basic case, if the function returns this value, midi file did not contain any melodies
    res = (-1, -1), (-1, -1), -1
    for i in range(len(Melodies_1[0])):
        for j in range(len(Melodies_2[1])):
            # for each track we go through, we find the most similar spot
            r1 = ClosestSequences(Melodies_1[0][i], Melodies_1[1][i], Melodies_2[0][j], Melodies_2[1][j], melody_length)
            if r1[1] > res[2] or res[2] == -1:
                res = (i, j), r1[0], r1[1]
    return res



# receives instances of series of notes and relative times and finds the most fitting parts
def ClosestSequences(Melody_1_Notes: list, Melody_1_Timings: list, Melody_2_Notes: list, Melody_2_Timings: list, sublength: int):
    if sublength == -1:
        sublength = min(len(Melody_1_Notes), len(Melody_2_Notes))
    if sublength > min(len(Melody_1_Notes), len(Melody_2_Notes)):
        raise Exception(f"Invalid sublist length - {len(Melody_1_Notes)}; {len(Melody_2_Notes)} < {sublength}")
    res = (-1, -1), -1
    for i in range(len(Melody_1_Notes) - sublength + 1):
        for j in range(len(Melody_2_Notes) - sublength + 1):
            helps = (Melody_1_Notes[i:i + sublength], Melody_2_Notes[j:j + sublength]), (Melody_1_Timings[i:i + sublength], Melody_2_Timings[j:j + sublength])
            similarity = ListDifference(helps[0][0], helps[0][1]) * MELODY_WEIGHT + ListDifference(helps[1][0], helps[1][1]) * TIMING_WEIGHT
            if similarity < res[1] or res[1] == -1:
                res = (i, j), similarity
    return res


def ListDifference(arr1: list, arr2: list):
    if len(arr1) != len(arr2):
        raise Exception(f"Invalid list length - {len(arr1)} {len(arr2)}")
    return sum([abs(arr1[i] - arr2[i]) for i in range(len(arr1))])


print(CompareMelodies("Temp1.mid", "Temp9.mid", 16))

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
