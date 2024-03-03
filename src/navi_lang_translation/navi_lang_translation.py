import requests

import morphology
import orthography

# user_input defined here for now, will be properly integrated in future versions
user_input = "frayhilvan faypay paypay fayfay payfay"
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
                morphology.get_verb_affixes(word_answers, inner_dict)
            elif part_speech in prefix_suffix_possible:
                morphology.get_other_affixes(word_input, word_answers, inner_dict)

            # Grab Reef spelling
            word_reef = orthography.get_reef_spelling(word_syllables, word_stress)
            inner_dict["reef"] = word_reef
            # Return syllables to match pronunciation of the word
            inner_dict["syllables"] = word_pronunciation.get("syllables")

            # Update stress to reflect affixes
            if inner_dict["aff:pre"] is not None:
                morphology.update_other_stress(word_input, inner_dict)
            elif inner_dict["aff:in"] is not None:
                morphology.update_verb_stress(inner_dict)

        nested_dict[word_input] = inner_dict

    return nested_dict


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
