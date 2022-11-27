# Python 3.6

import math
import csv
import sys

from collections import defaultdict
from decimal import Decimal

vote_ballots = []

with open("/Users/jelle/Downloads/STV template - Data.csv", 'r') as floor:
    votereader = csv.reader(floor, delimiter=',', quotechar='"')
    names = next(votereader)
    for row in votereader:
        # Vertaal de stemmingen na
        # ar arrays van preference
        # Dus een biljet met 2,1,x,x,x,x wordt:
        # [1, 0]
        r = [candidate for candidate, _ in sorted([(candidate, choice) for candidate, choice in enumerate(row) if choice], key=lambda x: x[1])]
        vote_ballots.append(r)

# # Verificatie dat de namen goed zijn ingelezen:
# for ballot in vote_ballots:
#     for i, person in enumerate(ballot):
#         print(f"{i+1}st choice: {names[person]}", end=", ")
#     print()

class Ballots:
    def __init__(self, value=None):
        if value is None:
            self.value = 0
            self.ballotvalue = True
        else:
            self.value = value
            self.ballotvalue = False
        self.ballots = []

    def add_ballot(self, ballot):
        self.ballots.append(ballot)
        if self.ballotvalue:
            self.value += 1

    def __iter__(self):
        return self.ballots.__iter__()

    def __len__(self):
        return self.ballots.__len__()

class VoteCounter:
    def __init__(self, ballots, names, positions):
        self.ballots = ballots
        self.names = names
        self.positions = positions

        self.quota = math.floor((len(vote_ballots) / (positions + 1)) + 1)
        self.disqualified = set()
        self.elected = set()
        self.counts = defaultdict(lambda: {"count": Decimal(0), "ballots": [Ballots()]})
        for i, ballot in enumerate(self.ballots):
            self.counts[ballot[0]]["count"] += 1
            self.counts[ballot[0]]["ballots"][0].add_ballot(ballot)

    def print_status(self):
        for person in self.counts:
            count = self.counts[person]["count"]
            if person in self.disqualified and not person in self.elected:
                print(f"{self.names[person]: <20}:      [ELIMINATED]")
                continue
            print(f"{self.names[person]: <20}: {count: >4}", end="")
            if count >= self.quota:
                print(" [ELECTED]", end="")
            if count > self.quota:
                surplus_amount = count - self.quota
                print(f" ({surplus_amount} surplus)", end="")
            print()
        print()

    def move_any_surplus(self):
        """Returns True if this was a surplus round"""
        surplus = []
        for person in self.counts:
            count = self.counts[person]["count"]
            if count >= self.quota:
                self.elected.add(person)
                self.disqualified.add(person)
            if count > self.quota:
                surplus_amount = Decimal(count - self.quota)
                surplus.append({"candidate": person, "surplus_amount": surplus_amount})
                self.counts[person]["count"] -= surplus_amount

        for surp in sorted(surplus, key=lambda x: x["surplus_amount"]):
            person = surp["candidate"]
            print(f"Checking next preference for all ballots for '{names[person]}'")
            increased = defaultdict(lambda: False)
            nr_ballots_increased = defaultdict(lambda: 0)
            ballots_len = len(self.counts[person]["ballots"][-1])
            for ballot in self.counts[person]["ballots"][-1]:
                nxt = self._next_qualified_candidate(ballot)
                if nxt is None:
                    # self.counts["unused"]["ballots"][0].add_ballot(ballot)
                    pass
                else:
                    print(f"'{self.names[nxt]}'", end=", ")
                    if not increased[nxt]:
                        increased[nxt] = True
                        self.counts[nxt]["ballots"].append(Ballots(surp["surplus_amount"]))
                    self.counts[nxt]["ballots"][-1].add_ballot(ballot)
                    nr_ballots_increased[nxt] += 1
            print()
            for person, nr in nr_ballots_increased.items():
                print(f"Increasing {self.names[person]} by {nr}/{ballots_len}")
                self.counts[person]["count"] += Decimal(nr) * Decimal(surp["surplus_amount"]) / Decimal(ballots_len)
            print()
        return len(surplus) > 0

    def exclude_any_candidates(self):
        if len(self.elected) >= self.positions:
            return
        lowest = sorted([(person, x["count"]) for person, x in self.counts.items() if person not in self.disqualified], key=lambda x: x[1])[0][0]
        self.disqualified.add(lowest)
        print(f"Excluding: '{self.names[lowest]}', checking next preferences")
        for ballot_group in self.counts[lowest]["ballots"]:
            increased = defaultdict(lambda: False)
            nr_ballots_increased = defaultdict(lambda: 0)
            for ballot in ballot_group:
                nxt = self._next_qualified_candidate(ballot)
                if nxt is None:
                    # self.counts["unused"]["ballots"][0].add_ballot(ballot)
                    pass
                else:
                    print(f"'{self.names[nxt]}'", end=", ")
                    if not increased[nxt]:
                        increased[nxt] = True
                        self.counts[nxt]["ballots"].append(Ballots(ballot_group.value))
                    self.counts[nxt]["ballots"][-1].add_ballot(ballot)
                    nr_ballots_increased[nxt] += 1
            print()
            for person, nr in nr_ballots_increased.items():
                # print(f"Increasing {self.names[person]} by {nr}/{ballot_group.value}")
                self.counts[person]["count"] += Decimal(nr) * Decimal(ballot_group.value) / Decimal(len(ballot_group))
        print()

    def _next_qualified_candidate(self, ballot):
        for elem in ballot:
            if elem not in self.disqualified:
                return elem
        return None

positions = 3
counter = VoteCounter(vote_ballots, names, positions)
counter.print_status()
while len(counter.elected) < positions:
    surplus = counter.move_any_surplus()
    if surplus:
        counter.print_status()
    else:
        counter.exclude_any_candidates()
        counter.print_status()
