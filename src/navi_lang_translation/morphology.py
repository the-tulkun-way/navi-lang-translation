# important variables
vlist = ["a", "e", "i", "o", "u", "ä", "é", "ì", "ù"]
pvlist = ["ll", "rr"]


def apply_lenition(word_to_lenite):
    leniting_sounds = {"px": "p", "tx": "t", "kx": "k", "p": "f", "t": "s", "k": "h", "ts": "s", "'": ""}
    processed_word = word_to_lenite

    # Correct early return for special cases
    if word_to_lenite.startswith("'rr") or word_to_lenite.startswith("'ll"):
        return processed_word
    else:
        for key, value in leniting_sounds.items():
            if word_to_lenite.startswith(key):
                if len(key) == 2:
                    processed_word = value + word_to_lenite[2:]
                else:
                    processed_word = value + word_to_lenite[1:]
                break
        return processed_word



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


def get_other_affixes(input_word, api_data, inner_dictionary):
    root_lenited = ""
    post_prefix_index = -1
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
            elif affix_type == "aff:suf" or affix_type == "adp" or affix_type == "adp:len":
                aff_suf.append(affix)

        # Check for the prefixes "kaw", "sna", and "munsna", which are not detected by the API
        # Account for below input words where the prefixes might be the same substring as the root
        if input_word != "paypay" or "faypay" or "payfay" or "fayfay":
            root_lenited = apply_lenition(inner_dictionary["root"])
            post_prefix_index = input_word.find(root_lenited)
        else:
            post_prefix_index = -1
        # Make sure a prefix substring exists
        if post_prefix_index != -1:
            prefix_substring = input_word[:post_prefix_index]
            if "kaw" in prefix_substring:
                aff_pre.append("kaw")
            if "munsna" in prefix_substring:
                aff_pre.append("munsna")
            elif "sna" in prefix_substring:
                aff_pre.append("sna")

    # Update the inner dictionary directly
    inner_dictionary["aff:pre"] = aff_pre if aff_pre else None
    inner_dictionary["aff:suf"] = aff_suf if aff_suf else None


def update_other_stress(input_word, inner_dictionary):
    prefixes = inner_dictionary["aff:pre"]
    root_lenited = ""
    post_prefix_index = -1
    # Initialize counters for vlist and pvlist matches
    vlist_count = 0
    pvlist_count = 0
    stress_shift = 0

    # Account for a lower stress number if a combination prefix is used
    # Find the index where the root begins (post prefixes) in the input_word
    if inner_dictionary["root"] != "pay":
        if any(prefix in ["pe", "me", "pxe", "ay"] for prefix in prefixes):
            root_lenited = apply_lenition(inner_dictionary["root"])
            post_prefix_index = input_word.find(root_lenited)
    # Account for input words "paypay"*, "faypay"*, "payfay", and "fayfay" where the prefixes might be the same substring as the root
    elif (inner_dictionary["root"] == "pay"):
        if "ay" in prefixes and any(prefix in ["pe", "fì"] for prefix in prefixes):
            post_prefix_index = 3

    # Make sure a prefix substring exists
    if post_prefix_index != -1:
        # Logic to test for combination prefixes
        combination_prefixes = any(combination in input_word[:post_prefix_index] \
                for combination in ["pem", "pep", "pay", "fay", "tsay", "fray"])
        has_combination_prefixes = any(all(x in prefixes for x in pair) \
                for pair in [("pe", "me"), ("pe", "pxe"), ("pe", "ay"), ("fì", "ay"), ("tsa", "ay"), ("fra", "ay")])
        if combination_prefixes and has_combination_prefixes:
            stress_shift -= 1

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


# Takes every substring and its information from substring_search() and returns a list of lists with
# only combinations of substrings that do not overlap or leave gaps and match the length of the main_string
def find_combinations(positions_list, word, current_combination=None, last_end_index=0, combos=None):
    word_length = len(word)
    
    if combos is None:
        combos = []
    if current_combination is None:
        current_combination = []

    for position in positions_list:
        start_index, end_index, _, _ = position
        # If starting a new combination, ensure the first entry starts at index 0
        if not current_combination and start_index != 0:
            continue  # Skip this position as it cannot start a new combination
        # Ensure the next tuple starts immediately after the last tuple in the combination
        elif start_index == last_end_index + 1 or (not current_combination and start_index == 0):
            new_combination = current_combination + [position]
            combos.append(new_combination)
            # Recurse with the updated current combination and the new last end index
            find_combinations(positions_list, word, new_combination, end_index, combos)

    # Filter combinations that don't end at the last character of the string
    combos = [entry for entry in combos if entry[-1][1] == word_length - 1]

    return combos


# Gathers every found substring in the main_string and relevant data for each instance
def substring_search(word, substring_dict):
    # Check which keys fit inside other keys
    positions = []
    for key in substring_dict:
        # Create a list of tuples to record the indices where each substring is found in the main string
        start = 0  # Start at the beginning of the string
        while True:
            # Use find to locate the substring, starting from 'start'
            start = word.find(key, start)
            if start == -1:  # No more instances found
                break
            # (starting index, ending index, substring found, valid positions of substring)
            new_tuple = (start, start + (len(key) - 1), key, substring_dict[key])
            positions.append(new_tuple)
            start += 1  # Move to the next position for the next search

    # Sorting the lists of tuples in place based on the first item of each tuple
    positions.sort(key=lambda x: x[0])
    # If no substrings were detected at the beginning of main_string, return an empty list
    if positions == [] or positions[0][0] > 0:
        return []
    else:
        return find_combinations(positions, word)


def check_for_valid_number2(lst, suffix):
    strings_to_check = ['zazam', 'zaza', 'vozam', 'voza', 'zam', 'za', 'vol', 'vo']

    # Track the last found index to ensure the order is correct
    last_found_index = -1

    # Check for issues with "vol" and "vo"
    # "Vol" and "vo" are both present
    if "vol" in lst and "vo" in lst:
        return False
    # "Vol" is in the list, but the suffix isn't "aw" or "vol" itself
    elif "vol" in lst and (suffix != "aw" and suffix != "vol"):
        return False
    # "Vo" is in the list, but the suffix is "aw" or "vo" itself
    elif "vo" in lst and (suffix == "aw" or suffix == "vo"):
        return False
    # Check for issues with "zazam" and "zaza"
    # "Zazam" and "zaza" are both present
    elif "zazam" in lst and "zaza" in lst:
        return False
    # "Zaza" is in the list, but it isn't the suffix itself
    elif "zaza" in lst and suffix != "zaza":
        return False
    # Check for issues with "vozam" and "voza"
    # "Vozam" and "voza" are both present
    elif "vozam" in lst and "voza":
        return False
    # "Voza" is in the list, but it isn't the suffix itself
    elif "voza" in lst and suffix != "voza":
        return False
    # Check for issues with "zam" and "za"
    # "Zam" and "za" are both present
    elif "zam" in lst and "za" in lst:
        return False
    # "Za" is in the list, but it isn't the suffix itself
    elif "za" in lst and suffix != "za":
        return False

    for item in lst:
        if item in strings_to_check:
            current_index = strings_to_check.index(item)

            # Check if the current item appears after the last found item in strings_to_check
            if current_index <= last_found_index:
                # The current item is out of order
                return False
            else:
                # Update last_found_index to current item's index
                last_found_index = current_index

    return True


def check_for_valid_number1(input_word):
    dict_of_substrings = {"vo": ["power"],
                      "vol": ["power", "dep_suffix"],
                      "zam": ["power"],
                      "za": ["power", "dep_suffix"],
                      "vozam": ["power"],
                      "voza": ["power", "dep_suffix"],
                      "zazam": ["power"],
                      "zaza": ["power", "dep_suffix"],
                      "me": ["prefix"],
                      "pxe": ["prefix"],
                      "be": ["prefix"],
                      "tsì": ["prefix"],
                      "mrr": ["prefix", "base_suffix", "dep_suffix"],
                      "pu": ["prefix"],
                      "ki": ["prefix"],
                      "aw": ["base_suffix", "dep_suffix"],
                      "mun": ["base_suffix"],
                      "pey": ["base_suffix", "dep_suffix"],
                      "sìng": ["base_suffix"],
                      "fu": ["base_suffix", "dep_suffix"],
                      "hin": ["base_suffix"],
                      "mu": ["dep_suffix"],
                      "sì": ["dep_suffix"],
                      "hi": ["dep_suffix"]}

    combinations = substring_search(input_word, dict_of_substrings)
    filtered_combinations = []
    last_was_power = False

    for list_of_tuples in combinations:
        n_tuples = len(list_of_tuples)
        is_valid = True  # Flag to track validity of the current list_of_tuples
        list_of_powers = []

        for index, item in enumerate(list_of_tuples):
            # Check if this tuple contains 'prefix'
            if 'prefix' in item[3]:
                # If it's not the first tuple and the last tuple didn't contain 'power', continue
                if index > 0 and not last_was_power:
                    is_valid = False
                    break  # Exit the loop early since this list fails the check
                # If it's the last tuple, continue
                elif index == n_tuples - 1:
                    is_valid = False
                    break

            # If substring is a suffix but not in the final tuple, continue
            if ("base_suffix" in item[3] or "dep_suffix" in item[3]) and (index != n_tuples - 1):
                is_valid = False
                break

            # Update last_was_power flag for next iteration
            last_was_power = 'power' in item[3]

            if "power" in item[3]:
                list_of_powers.append(item[2])

        # If is_valid is False, the current list_of_tuples failed checks, so skip it
        if not is_valid:
            continue

        # If all conditions met so far, check that each present power is in the correct order
        suffix = list_of_tuples[-1][2]
        if check_for_valid_number2(list_of_powers, suffix):
            filtered_combinations.append(list_of_tuples)

    return filtered_combinations
