import requests

vlist = ["a", "e", "i", "o", "u", "ä", "é", "ì", "ù"]
pvlist = ["ll", "rr"]

# user_input defined here for now, will be properly integrated in future versions
user_input = "leymkem"
response = requests.get("https://reykunyu.wimiso.nl/api/fwew?t%C3%ACpawm=" + user_input).json()


def build_dict():
    nested_dict = {}
    infix_possible = ["n:si", "v:?", "v:in", "v:tr", "v:m", "v:si", "v:cp", "nv:si"]
    prefix_suffix_possible = ["n", "n:unc", "n:pr", "n:pn", "adj", "adv", "inter"]
    syl_exceptions = {  # needed to transfer into Reef spelling
        "tuté": "tu-té", "fìtseng(e)": "fì-tse-nge", "oetsyìp": "o-e-tsyìp",
        "fpomtokxnga'": "fpom-tokx-nga'", "kefpomtokxnga'": "ke-fpom-tokx-nga'",
        "tsankumnga'": "tsan-kum-nga'", "tsankum": "tsan-kum", "srankehe": "sran-ke-he",
        "tstunkem": "tstun-kem", "tsunkemtsyìp": "tstun-kem-tsyìp",
        "tìleymkem": "tì-leym-kem", "säleymkem": "sä-leym-kem",
        "leymkem": "leym-kem", "nìayoeng": "nì-ay-o-eng", "zenke": "zen-ke"
    }

    for word in response:
        word_input = word.get("tìpawm")
        inner_dict = {
            "valid": False,
            "root": None,
            "reef": None,
            "forest IPA": None,
            "reef IPA": None,
            "part of speech": None,
            "stress": None,
            "syllables": None,
            "aff:pre": None,
            "aff:suf": None,
            "aff:in": None,
            "infix loc.": None
        }

        if word.get("sì'eyng"):
            # Set valid to True if the API returns data
            inner_dict["valid"] = True

            word_answers = word.get("sì'eyng")[0]
            # Grab the root word from the API
            word_root = word_answers.get("na'vi")
            inner_dict["root"] = word_root
            # Grab the part of speech from the API
            part_speech = word_answers.get("type")
            inner_dict["part of speech"] = part_speech

            word_pronunciation = word_answers.get("pronunciation")[0]
            # Grab the IPA for each dialect from the API
            forest_ipa = word_pronunciation.get("ipa").get("FN")
            inner_dict["forest IPA"] = forest_ipa
            reef_ipa = word_pronunciation.get("ipa").get("RN")
            inner_dict["reef IPA"] = reef_ipa
            # Grab the number of the stressed syllable from the API
            word_stress = word_pronunciation.get("stressed")
            inner_dict["stress"] = word_stress
            # Grab the syllables from the API
            # If part of the syllable exceptions, alter them so Reef spelling will be accurate
            if word_root in syl_exceptions:
                word_syllables = syl_exceptions[word_root]
            else:
                word_syllables = word_pronunciation.get("syllables")
            inner_dict["syllables"] = word_syllables

            # Grab the affixes from the API
            # Depending on the part of speech, affixes are processed differently
            if part_speech in infix_possible:
                get_verb_affixes(word_answers, inner_dict)
            elif part_speech in prefix_suffix_possible:
                get_other_affixes(word_answers, inner_dict)

            # Grab Reef spelling
            word_reef = get_reef_spelling(word_syllables, word_stress)
            inner_dict["reef"] = word_reef
            # Return syllables to match pronunciation of the word
            inner_dict["syllables"] = word_pronunciation.get("syllables")

            # Update stress to reflect affixes
            if inner_dict["aff:pre"] is not None:
                update_other_stress(inner_dict)
            elif inner_dict["aff:in"] is not None:
                update_verb_stress(inner_dict)

        nested_dict[word_input] = inner_dict

    return nested_dict


def break_into_syllables():
    pass


def get_verb_affixes(api_data, inner_dictionary):
    word_conjugated = api_data.get("conjugated")[0]
    word_affixes = word_conjugated.get("affixes", [])
    infixes = []

    for affix_data in word_affixes:  # Iterate directly through the list
        if isinstance(affix_data.get("affix"), str):
            infixes.append(affix_data.get("affix"))
        elif isinstance(affix_data.get("affix"), dict):
            infixes.append(affix_data.get("affix").get("na'vi"))
        else:
            print("Error. affix_data.get(\"affix\") didn't return a str or dict as expected.")

    # Update the inner dictionary directly to include verb infixes
    inner_dictionary["aff:in"] = infixes if infixes else None

    # Update the inner dictionary directly to include verb infix locations
    word_infixloc = api_data.get("infixes")
    inner_dictionary["infix loc."] = word_infixloc if word_infixloc else None


def get_other_affixes(api_data, inner_dictionary):
    # Initialize lists for prefixes and suffixes
    aff_pre = []
    aff_suf = []

    if api_data.get("conjugated"):
        word_conjugated = api_data.get("conjugated")[0]
        # word_conjugation = word_conjugated.get("conjugation")

        # Ensure 'affixes' key exists and is iterable
        word_affixes = word_conjugated.get("affixes", [])
        for affix_data in word_affixes:
            affix_navi = affix_data.get("affix")
            affix_type = affix_navi.get("type")
            affix = affix_navi.get("na'vi")
            if affix_type == "aff:pre" or affix_type == "aff:pre:len":
                aff_pre.append(affix)
            elif affix_type == "aff:suf" or affix_type == "adp":
                aff_suf.append(affix)

    # Update the inner dictionary directly
    inner_dictionary["aff:pre"] = aff_pre if aff_pre else None
    inner_dictionary["aff:suf"] = aff_suf if aff_suf else None


def update_other_stress(inner_dictionary):
    prefixes = inner_dictionary["aff:pre"]
    # Initialize counters for vlist and pvlist matches
    vlist_count = 0
    pvlist_count = 0
    stress_shift = 0

    # Make updates to the stress shift number based on prefix syllables (identified by counting vowels/pseudovowels)
    for prefix in prefixes:
        # Check each character in a prefix for vlist matches
        for char in prefix:
            if char in vlist:
                vlist_count += 1
        # Check each pair of characters in a prefix for pvlist matches
        # Use a sliding window of size 2 to check pairs
        for i in range(len(prefix) - 1):
            pair = prefix[i:i + 2]
            if pair in pvlist:
                pvlist_count += 1
    stress_shift += vlist_count + pvlist_count

    # Update the inner dictionary directly
    inner_dictionary["stress"] += stress_shift


def update_verb_stress(inner_dictionary):
    # Prepare variables needed to update the stress if infixes are present
    second_in = ["ei", "äng", "uy", "ats"]  # list of second position infixes
    # Initialize counters for vlist and pvlist matches
    vlist_count = 0
    pvlist_count = 0
    stress_shift = 0
    infixloc_root = inner_dictionary["infix loc."]
    combined_list = vlist + pvlist
    period_positions = [i for i, letter in enumerate(infixloc_root) if letter == '.']
    instances = []
    stressed_vowel = inner_dictionary["stress"]
    before_infixes = False
    between_infixes = False
    after_infixes = False

    # Check for exception words and update base stress accordingly
    if inner_dictionary["root"] == "omum" or "inan":
        stressed_vowel = 1
        inner_dictionary["stress"] = 1

    # Search through the word to find instances of any item from the combined list
    for i in range(len(infixloc_root)):
        for item in combined_list:
            if infixloc_root[i:i + len(item)] == item:
                instances.append((i, item))  # Store position and value of each instance
    stressed_vowel_pos = instances[stressed_vowel - 1][0]
    if stressed_vowel_pos > period_positions[1]:
        after_infixes = True
    elif stressed_vowel_pos < period_positions[0]:
        before_infixes = True
    elif period_positions[0] < stressed_vowel_pos < period_positions[1]:
        between_infixes = True

    if between_infixes:
        # Make updates to the stress shift number based on prefix syllables (identified by counting vowels/pseudovowels)
        for infix in inner_dictionary["aff:in"]:
            if infix not in second_in:
                # Check each character in a prefix for vlist matches
                for char in infix:
                    if char in vlist:
                        vlist_count += 1
                # Check each pair of characters in a prefix for pvlist matches
                # Use a sliding window of size 2 to check pairs
                for i in range(len(infix) - 1):
                    pair = infix[i:i + 2]
                    if pair in pvlist:
                        pvlist_count += 1
    elif after_infixes:
        # Make updates to the stress shift number based on infix syllables (identified by counting vowels/pseudovowels)
        for infix in inner_dictionary["aff:in"]:
            # Check each character in an infix for vlist matches
            for char in infix:
                if char in vlist:
                    vlist_count += 1
            # Check each pair of characters in an infix for pvlist matches
            # Use a sliding window of size 2 to check pairs
            for i in range(len(infix) - 1):
                pair = infix[i:i + 2]
                if pair in pvlist:
                    pvlist_count += 1
    stress_shift += vlist_count + pvlist_count

    # Update the inner dictionary directly
    inner_dictionary["stress"] += stress_shift


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


# Run the code
def run_code():
    if user_input != "":
        our_dict = build_dict()
        # Display the dictionary built for each input word
        for key, value in our_dict.items():
            print(f"{key}:")
            for inner_key, inner_value in value.items():
                print(f"  {inner_key}: {inner_value}")
            print()  # adds a line break
    else:
        print("Error. No input.")


run_code()
