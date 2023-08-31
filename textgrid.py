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
    dist_matrix = _levenshtein_distance_matrix(string1, string2,
                                               is_damerau=is_damerau)
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
            # if i > 0 and j > 0:
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



def get_mapping(user_textgrid, bot_textgrid):
    tg1 = textgrids.TextGrid()
    tg2 = textgrids.TextGrid()

    tg1.read(user_textgrid)
    tg2.read(bot_textgrid)

    items1 = extract(tg1)
    items2 = extract(tg2)

    words1 = [item['word'] for item in items1]
    words2 = [item['word'] for item in items2]

    # word level operations.
    word_ops = get_ops(words1, words2, is_damerau=True)

    shift = 0  # shift in the index of words1
    for op in word_ops:
        i, j = op[1], op[2]
        if op[0] == 'delete':  #
            if 'ops' not in items1[i]:
                items1[i]['ops'] = []

            items1[i]['ops'].append('delete "' + words1[i + shift] + '"')
            items1[i]['matched_phones'] = []  # set empty phones
            items1[i]['matched_xmin'] = items2[j]['xmin']
            items1[i]['matched_xmax'] = items2[j]['xmax']

            del words1[i + shift]
            shift -= 1
        elif op[0] == 'insert':
            if i + 1 >= len(items1):
                items1.append({'word': words2[j], 'ops': []})
                op_msg = 'auto inserted a "' + words2[j] + '"'
            else:
                op_msg = 'insert a "' + words2[j] + '"'

            if 'ops' not in items1[i + 1]:
                items1[i + 1]['ops'] = []
            items1[i + 1]['ops'].append(op_msg)
            # items1[i + 1]['matched_phones'] = items2[j]['phones']

            items1[i + 1]['matched_xmin'] = items2[j+1 if j+1 < len(items2) else j]['xmin']
            items1[i + 1]['matched_xmax'] = items2[j+1 if j+1 < len(items2) else j]['xmax']

            words1.insert(i + shift + 1, words2[j])
            shift += 1
        elif op[0] == 'replace':
            if 'ops' not in items1[i]:
                items1[i]['ops'] = []

            items1[i]['ops'].append('replace with "' + words2[j] + '"')
            #print("replacing", words1[i + shift], "with", words2[j], i, j)

            items1[i]['matched_phones'] = items2[j]['phones']

            items1[i]['matched_xmin'] = items2[j]['xmin']
            items1[i]['matched_xmax'] = items2[j]['xmax']

            words1[i + shift] = words2[j]
        elif op[0] == 'transpose':
            if 'ops' not in items1[i]:
                items1[i]['ops'] = []
            if 'ops' not in items1[j]:
                items1[j]['ops'] = []

            print("transposing", words1[i + shift], "with", words1[j + shift], i, j)
            items1[i]['ops'].append('swap with "' + words1[j + shift] + '"')
            items1[i]['matched_phones'] = items2[j]['phones']
            items1[i]['matched_xmin'] = items2[j]['xmin']
            items1[i]['matched_xmax'] = items2[j]['xmax']

            items1[j]['ops'].append('swap with "' + words1[i + shift] + '"')
            items1[j]['matched_phones'] = items2[i]['phones']
            items1[j]['matched_xmin'] = items2[i]['xmin']
            items1[j]['matched_xmax'] = items2[i]['xmax']
            words1[i + shift], words1[j + shift] = words1[j + shift], words1[i + shift]


    # phone level operations.
    index = -1
    for item1 in items1:
        if 'matched_phones' in item1:  # phones/word have been matched already
            item2_phones = item1['matched_phones']
        else:
            for i, item2 in enumerate(items2):
                if i <= index:  # skip the matched words
                    continue

                if item1['word'] == item2['word']:
                    item1['matched_xmin'] = item2['xmin']
                    item1['matched_xmax'] = item2['xmax']
                    item2_phones = item2['phones']
                    index = i
                    break
            else:
                continue  # did not find match for this word (should not happen)

        # match phones
        #print(item2_phones)
        phones1 = [item['phone'] for item in item1['phones']]
        phones2 = [item['phone'] for item in item2_phones]

        phone_ops = get_ops(phones1, phones2, is_damerau=True)
        print(phone_ops)
        shift = 0
        for op in phone_ops: # phone level operations
            i, j = op[1], op[2]
            if op[0] == 'delete':  #
                if 'ops' not in item1['phones'][i]:
                    item1['phones'][i]['ops'] = []
                item1['phones'][i]['ops'].append('delete "' + phones1[i + shift] + '"')
                del phones1[i + shift]
                shift -= 1
            elif op[0] == 'insert':
                if i + 1 >= len(item1['phones']):
                    item1['phones'].append({'phone': phones2[j], 'ops': []})
                    op_msg = 'auto inserted a "' + phones2[j] + '"'
                else:
                    op_msg = 'insert a "' + phones2[j] + '"'

                if 'ops' not in item1['phones'][i+1]:
                    item1['phones'][i+1]['ops'] = []
                item1['phones'][i+1]['ops'].append(op_msg)
                phones1.insert(i + shift + 1, phones2[j])
                shift += 1
            elif op[0] == 'replace':
                if 'ops' not in item1['phones'][i]:
                    item1['phones'][i]['ops'] = []
                item1['phones'][i]['ops'].append('replace with "' + phones2[j] + '"')
                phones1[i + shift] = phones2[j]
            elif op[0] == 'transpose':
                if 'ops' not in item1['phones'][i]:
                    item1['phones'][i]['ops'] = []
                if 'ops' not in item1['phones'][j]:
                    item1['phones'][j]['ops'] = []


                item1['phones'][i]['ops'].append('swap with "' + phones1[j + shift] + '"')
                item1['phones'][j]['ops'].append('swap with "' + phones1[i + shift] + '"')

                phones1[i + shift], phones1[j + shift] = phones1[j + shift], phones1[i + shift]

    return items1

    """
    Hello, 
    
    
    K W EH1 SH AH0 N - user
    K W EH1 S CH AH0 N - bot
    ('insert', 2, 3), ('replace', 3, 4)
    
    K 
    W 
    EH1 
    S <- missing (red)
    CH <- replace SH with CH
    AH0 
    N
    
    (type, i, j)
    insert the bot[i+1] to user[j]
    """


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

