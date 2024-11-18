from mido import *
import editdistance
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


def PresentNotes(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        for j in i:
            if hasattr(j, "note") and j.note not in res:
                res.append(j.note)
    return res


def NoteLength(file, note):
    f = MidiFile(file, clip=True)
    for i in f.tracks:
        start = False
        count = 0
        for j in i:
            if start and hasattr(j, "note"):
                count += j.time
            if hasattr(j, "note") and j.note == note and j.type == "note_on":
                start = True
            if hasattr(j, "note") and j.note == note and j.type == "note_off":
                return count

    pass


def NoteSequences(file):
    f = MidiFile(file, clip=True)
    res = []
    for i in f.tracks:
        res1 = []
        for j in i:
            if hasattr(j, "note") and j.type == "note_on":
                res1.append(j.note)
        res1 = res1[:-4]
        res.append(res1)
    return res


def CompareSequences(file1, file2, melody_length=7):
    arr1, arr2 = NoteSequences(file1), NoteSequences(file2)
    res = (-1, -1), (-1, -1), -1
    for i in range(len(arr1)):
        for j in range(len(arr2)):
            r1 = ClosestMelodies(arr1[i], arr2[i], melody_length)
            if r1[1] > res[2] or res[2] == -1:
                res = (i, j), r1[0], r1[1]
    return res


def smth():
    pass


def ClosestMelodies(arr1: list, arr2: list, sublength: int):
    if sublength > min(len(arr1), len(arr2)):
        raise Exception(f"Invalid sublist length - {len(arr1)} {len(arr2)} < {sublength}")
    res = (-1, -1), -1
    for i in range(len(arr1)-sublength+1):
        for j in range(len(arr2)-sublength+1):
            if Helps(arr1[i:i+sublength], arr2[j:j+sublength]) < res[1] or res[1] == -1:
                res = (i, j), Helps(arr1[i:i+sublength], arr2[j:j+sublength])
    return res


def Helps(arr1: list, arr2: list):
    if len(arr1) != len(arr2):
        raise Exception(f"Invalid list length - {len(arr1)} {len(arr2)}")
    return sum([abs(arr1[i] - arr2[i]) for i in range(len(arr1))])


def ClosestTiming():
    pass


def manhattan_distance(list1, list2):
    distance = 0
    for sub1, sub2 in zip(list1, list2):
        sub_distance = 0
        for x, y in zip(sub1, sub2):
            sub_distance += abs(x - y)
        distance += sub_distance
    return distance


def compare_midi_files2(file1, file2):
    # Load midi files
    mid1 = MidiFile(file1)
    mid2 = MidiFile(file2)

    # Extract notes from midi files and group adjacent pitches together
    notes1 = []
    for msg in merge_tracks(mid1.tracks):
        if 'note_on' in msg.type:
            pitch = msg.note
            if notes1 and pitch == notes1[-1][-1] + 1:
                # Append pitch to last group
                notes1[-1].append(pitch)
            else:
                # Create new group for pitch
                notes1.append([pitch])

    notes2 = []
    for msg in merge_tracks(mid2.tracks):
        if 'note_on' in msg.type:
            pitch = msg.note
            if notes2 and pitch == notes2[-1][-1] + 1:
                # Append pitch to last group
                notes2[-1].append(pitch)
            else:
                # Create new group for pitch
                notes2.append([pitch])

    # Calculate similarity for each group of pitches
    similarity_scores = []
    return manhattan_distance(notes1, notes2)


print(compare_midi_files2("Temp3.mid", "Temp2.mid"))

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

#p rint(CompareSequences("Temp2.mid", "Temp1.mid"))


# for i in range(1, len(Temps[1].tracks[0])):
#     if hasattr(Temps[1].tracks[0][i], "type") and Temps[1].tracks[0][i].type == 'note_on' \
#             and Temps[1].tracks[0][i-1].type == "note_off" and Temps[1].tracks[0][i-1].time != 0:
#         Temps[1].tracks[0][i].time = 0
#
# print(Temps[1].tracks[0][:10])
#
#
# Temps[1].save("new_song.mid")
