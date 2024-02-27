# important variables
vlist = ["a", "e", "i", "o", "u", "ä", "é", "ì", "ù"]
pvlist = ["ll", "rr"]


def replace_prefix(s, old_prefix, new_prefix):
    if isinstance(s, str):
        if s == "UNK":
            return s  # Return the string as is if it is "UNK"
        if s.startswith(old_prefix):
            s = new_prefix + s[len(old_prefix):]
    return s


def combine_syllable_strings(list_with_substrings):
    combined_string = ""

    for item in list_with_substrings:
        # Check if the item is a string and not "UNK"
        if isinstance(item, str) and item != "UNK":
            combined_string += item
        elif item == "UNK":
            combined_string = "UNK"

    return combined_string


def replace_substring(s, old_substring, new_substring):
    if isinstance(s, str):
        if s == "UNK":
            return s  # Return the string as is if it is "UNK"
        s = s.replace(old_substring, new_substring)
    return s


def get_reef_spelling(syllables, stress_num):
    # Remove hyphens and place each syllable into a list as separate strings
    reef_list = syllables.split("-")
    if not isinstance(stress_num, int):
        stress_num = "UNK"
    reef_list.append(stress_num)

    # Change px/tx/kx to b/d/g
    # Change sy/tsy to sh/ch
    for index, item in enumerate(reef_list):
        reef_list[index] = replace_prefix(item, "px", "b")
        reef_list[index] = replace_prefix(reef_list[index], "tx", "d")
        reef_list[index] = replace_prefix(reef_list[index], "kx", "g")
        # The below lines of code are commented out as these prefixes are not traditionally used in Reef
        # reef_list[index] = replace_prefix(reef_list[index], "sy", "sh")
        # reef_list[index] = replace_prefix(reef_list[index], "tsy", "ch")

    # Prepare to sub "ä" with "e"
    for index, item in enumerate(reef_list):
        # Check if the item is a string and replace "ä" with "e"
        if isinstance(item, str):
            reef_list[index] = item.replace("ä", "e")

    # Prepare to remove the apostrophe between different vowels
    for index, item in enumerate(reef_list):
        # The item is a string and not "UNK" and starts with an '
        if (isinstance(item, str) and item != "UNK" and item.startswith("'")
                # The item has more than 1 char and its second character is in vlist
                and len(item) > 1 and item[1] in vlist
                # The item is not the first in the list and the item before is a string
                and index > 0 and isinstance(reef_list[index - 1], str)
                # The last character of the item before is in vlist
                and reef_list[index - 1][-1] in vlist
                # And that char is different from the current item's second char
                and item[1] != reef_list[index - 1][-1]):
            reef_list[index] = item[1:]

    for index, item in enumerate(reef_list):
        # The item is a string and not "UNK" and ends with an '
        if (isinstance(item, str) and item != "UNK" and item.endswith("'")
                # The item has more than 1 char and its second to last character is in vlist
                and len(item) > 1 and item[-2] in vlist
                # The item is not the last in the list and the item after is a string
                and index < len(reef_list) - 1 and isinstance(reef_list[index + 1], str)
                # The first character of the item after is in vlist
                and reef_list[index + 1][0] in vlist
                # And that char is different from the current item's second to last char
                and item[-2] != reef_list[index + 1][0]):
            reef_list[index] = item[:-1]

    # Account for assimilation in Reef pronunciation
    comb_reef_string = combine_syllable_strings(reef_list)

    comb_reef_string = replace_substring(comb_reef_string, "pxb", "bb")
    comb_reef_string = replace_substring(comb_reef_string, "pxd", "bd")
    comb_reef_string = replace_substring(comb_reef_string, "pxg", "bg")
    comb_reef_string = replace_substring(comb_reef_string, "txb", "db")
    comb_reef_string = replace_substring(comb_reef_string, "txd", "dd")
    comb_reef_string = replace_substring(comb_reef_string, "txg", "dg")
    comb_reef_string = replace_substring(comb_reef_string, "kxb", "gb")
    comb_reef_string = replace_substring(comb_reef_string, "kxd", "gd")
    comb_reef_string = replace_substring(comb_reef_string, "kxg", "gg")

    return comb_reef_string
