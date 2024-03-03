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
