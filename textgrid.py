# https://stackoverflow.com/questions/44640570/modify-damerau-levenshtein-algorithm-to-track-transformations-insertions-delet
# glegoux
import numpy as np
import textgrids


def levenshtein_distance(string1, string2):
    n1 = len(string1)
    n2 = len(string2)
    return _levenshtein_distance_matrix(string1, string2)[n1, n2]


def damerau_levenshtein_distance(string1, string2):
    n1 = len(string1)
    n2 = len(string2)
    return _levenshtein_distance_matrix(string1, string2, True)[n1, n2]


def get_ops(string1, string2, is_damerau=False):
    dist_matrix = _levenshtein_distance_matrix(string1, string2, is_damerau=is_damerau)
    i, j = dist_matrix.shape
    i -= 1
    j -= 1
    ops = list()
    while i != -1 and j != -1:
        if is_damerau:
            if i > 1 and j > 1 and string1[i - 1] == string2[j - 2] and string1[
                i - 2] == string2[j - 1]:
                if dist_matrix[i - 2, j - 2] < dist_matrix[i, j]:
                    ops.insert(0, ('transpose', i - 1, i - 2))
                    i -= 2
                    j -= 2
                    continue
        index = np.argmin([dist_matrix[i - 1, j - 1], dist_matrix[i, j - 1],
                           dist_matrix[i - 1, j]])

        if index == 0:
            if dist_matrix[i, j] > dist_matrix[i - 1, j - 1]:
                ops.insert(0, ('replace', i - 1, j - 1))
            i -= 1
            j -= 1
        elif index == 1:
            #if i > 0 and j > 0:
            ops.insert(0, ('insert', i - 1, j - 1))
            j -= 1
        elif index == 2:
            ops.insert(0, ('delete', i - 1, i - 1))
            i -= 1
    return ops

"""
strl = "AOR" # -> [A, O, R]
strl = [A, O, R] # -> [A, O, R]
"""

def execute_ops(ops, string1, string2):
    print(string1)
    print(string2)
    strings = [string1]
    string = list(string1)
    shift = 0
    for op in ops:
        i, j = op[1], op[2]
        if op[0] == 'delete':
            del string[i + shift]
            shift -= 1
        elif op[0] == 'insert':
            string.insert(i + shift + 1, string2[j])
            shift += 1
        elif op[0] == 'replace':
            string[i + shift] = string2[j]
        elif op[0] == 'transpose':
            string[i + shift], string[j + shift] = string[j + shift], string[
                i + shift]
        strings.append(''.join(string))
    return strings


def _levenshtein_distance_matrix(string1, string2, is_damerau=False):
    n1 = len(string1)
    n2 = len(string2)
    d = np.zeros((n1 + 1, n2 + 1), dtype=int)
    for i in range(n1 + 1):
        d[i, 0] = i
    for j in range(n2 + 1):
        d[0, j] = j
    for i in range(n1):
        for j in range(n2):
            if string1[i] == string2[j]:
                cost = 0
            else:
                cost = 1
            d[i + 1, j + 1] = min(d[i, j + 1] + 1,  # insert
                                  d[i + 1, j] + 1,  # delete
                                  d[i, j] + cost)  # replace
            if is_damerau:
                if i > 0 and j > 0 and string1[i] == string2[j - 1] and string1[
                    i - 1] == string2[j]:
                    d[i + 1, j + 1] = min(d[i + 1, j + 1],
                                          d[i - 1, j - 1] + cost)  # transpose
    return d

def extract(textgrid):
    items = []
    for item in textgrid.items():
        if item[0] == "words":
            for interval in item[1]:
                if interval.text == '':
                    continue
                word = {
                    'word': interval.text,
                    'xmin': interval.xmin,
                    'xmax': interval.xmax,
                    'phones': []
                }
                items.append(word)

        elif item[0] == "phones":
            for interval in item[1]:
                phone = {
                    'phone': interval.text,
                    'xmin': interval.xmin,
                    'xmax': interval.xmax,
                }

                for word in items:  # find the word that this phone belongs to
                    if word["xmin"] <= phone["xmin"] and word["xmax"] >= \
                            phone["xmax"]:
                        word["phones"].append(phone)

    return items


def get_comparison(user_textgrid, bot_textgrid):
    tg1 = textgrids.TextGrid()
    tg2 = textgrids.TextGrid()

    tg1.read(user_textgrid)
    tg2.read(bot_textgrid)

    items1 = extract(tg1)
    items2 = extract(tg2)

    words1 = [item['word'] for item in items1]
    words2 = [item['word'] for item in items2]

    print('=== damerau_levenshtein_distance for words ===')
    word_ops = get_ops(words1, words2, is_damerau=True)
    print('user: ', ' '.join(words1))
    print('bot:  ', ' '.join(words2))
    print(word_ops)


    # issue with duplicate words
    # TODO USE levenshtein word ops to get matching word if it exists
    index = -1
    for word in words2:  # words in bot
        matching_word = None
        for j, item in enumerate(items1):
            if index >= j:
                continue

            if item['word'] == word:
                matching_word = item
                index = j
                break

        if matching_word is None:  # probably removed word
            continue

        if word in words1:
            phones1, phones2 = [], []

            for item in items1:
                if item['word'] == word:
                    phones1 = list(map(lambda x: x['phone'], item['phones']))
                    break
            for item in items2:
                if item['word'] == word:
                    phones2 = list(map(lambda x: x['phone'], item['phones']))
                    break

            print('=== damerau_levenshtein_distance for phones ===')
            ops = get_ops(phones1, phones2, is_damerau=True)

            matching_word['phone_ops'] = ops

            print('user: ', phones1)
            print('bot:  ', phones2)
            print(ops)

    return items1, items2, word_ops
