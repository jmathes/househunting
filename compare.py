places = [
    ('Quarantine Enforcement Platform', 'https://tinyurl.com/QEP-TJ2023'),
    ('Possum Lodge', 'https://tinyurl.com/PossumLodge-TJ2023'),
    ("Hilbert's Paradox", 'https://tinyurl.com/HilbertParadox'),
    ('Highgarden', 'https://tinyurl.com/HighGarden-TJ2023'),
    ('Ravenholm', 'https://tinyurl.com/ravenholm-tj2024'),
    ('Ghost Forest', 'https://tinyurl.com/GhostForest-TJ2023'),
    ('Schenectady Prime', 'https://tinyurl.com/SchenecPrime'),
    ('Windgap Seitch', 'https://tinyurl.com/WindgapSietch'),
    ('Tamaranch', 'https://tinyurl.com/Tamaranch'),
    ('Attlerock', 'https://tinyurl.com/attlerock'),
    ('Ghostgate', 'https://tinyurl.com/GhostGate-TJ2023'),
    ('Stardew Valley', 'https://tinyurl.com/Stardew-Valley-TJ'),
    ('Hateno', 'https://tinyurl.com/Hateno-TJ2023'),
    ('Ordon Ranch', 'https://tinyurl.com/OrdonRanch'),
    ('Beauxbatons', 'https://tinyurl.com/Beauxbatons-TJ2023'),
    ('Turtle Rock', 'https://tinyurl.com/TurtleRock-TJ2023'),
    ('Quantum Grove', 'https://tinyurl.com/QuantumGrove'),
    ('Black Mesa', 'https://tinyurl.com/BlackMesa-TJ2023'),
    ('Blackwood', 'https://tinyurl.com/BlackWood-TJ2023'),
    ('Ash Twin', 'https://tinyurl.com/Ash-Twin'),
    ('Face Shrine', 'https://tinyurl.com/FaceShrine'),
    ('Timber Hearth', 'https://tinyurl.com/TimberHearth'),
    ('Spectacle Rock', 'https://tinyurl.com/SpectacleRock'),
    ('Bree', 'https://tinyurl.com/Bree-TJ2024'),
]

import functools
import os
import pprint
import random

random.shuffle(places)

def ml(s, l):
    return s + " " * (l - len(s))

@functools.lru_cache
def compare(p1, p2):
    yn = "asdf"
    namelen = max(len(p[0]) for p in places) + 1
    urllen = max(len(p[1]) for p in places) + 1
    os.system(f"open {p1[1]}")
    os.system(f"open {p2[1]}")
    while not yn.strip().lower() == "<" and not yn.strip().lower() == ">":
        question = ml(p1[0], namelen) + ml(p1[1], urllen) + "< or >" + ml(p2[0], namelen) + ml(p2[1], urllen) + ": "
        question = ml(p1[1], urllen) + " vs " + ml(p2[1], urllen) + "? (</>): "
        yn = input(question)
    if yn.strip().lower() == "<":
        return -1
    return 1

def guesstimate_comparisons(places):
    comparison_counts = []
    def count_comparisons(p1, p2):
        comparison_counts[-1] += 1
        return random.choice([1, -1])
    for i in range(10000):
        comparison_counts.append(0)
        sorted(places, key=functools.cmp_to_key(count_comparisons))
    print(f"You'll make probably between {min(comparison_counts)} and {max(comparison_counts)} comparisons, averaging {int(sum(comparison_counts) / len(comparison_counts) + 0.5)}")

guesstimate_comparisons(places)
pprint.pprint(sorted(places, key=functools.cmp_to_key(compare)))