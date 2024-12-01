from mido import *
import editdistance

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
TIMING_WEIGHT = 0.5
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


def PairedSequenses(file):
    a = []
    b = NoteSequences(file), TimingSequences(file)
    for i in range(len(b[1])):
        a.append(list(zip(b[0][i], b[1][i])))
    return a


# takes all the tracks from 2 midi files and finds the most similar melody, gives the indexes of melodies and the staring point at which the most suitability was found
# MAIN FUNC FOR NOW!!!
def CompareMelodies(file1, file2, melody_length=-1):
    arr1, arr2 = PairedSequenses(file1), PairedSequenses(file2)
    res = (-1, -1), (-1, -1), -1
    for i in range(len(arr1)):
        for j in range(len(arr2)):
            r1 = ClosestSequences(arr1[i], arr2[i], melody_length)
            if r1[1] > res[2] or res[2] == -1:
                res = (i, j), r1[0], r1[1]
    return res



# receives instances of series of notes and relative times and finds the most fitting parts
def ClosestSequences(arr1, arr2: list, sublength: int):
    if sublength == -1:
        sublength = min(len(arr1), len(arr2))
    if sublength > min(len(arr1), len(arr2)):
        raise Exception(f"Invalid sublist length - {len(arr1)}; {len(arr2)} < {sublength}")
    res = (-1, -1), -1
    for i in range(len(arr1) - sublength + 1):
        for j in range(len(arr1) - sublength + 1):
            help = (arr1[i:i + sublength][0], arr2[j:j + sublength][0]), (arr1[i:i + sublength][1], arr2[j:j + sublength])[1]
            similarity = ListDifference(help[0][0], help[0][1]) * MELODY_WEIGHT + ListDifference(help[1][0], help[1][1]) * TIMING_WEIGHT
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


def ListDifference(arr1: list, arr2: list):
    if len(arr1) != len(arr2):
        raise Exception(f"Invalid list length - {len(arr1)} {len(arr2)}")
    return sum([diff(arr1[i], arr2[i]) for i in range(len(arr1))])

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
