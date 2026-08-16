# Codeforces: 1890A - Doremy's Paint 3
# Problem Description: Determine whether the array can be rearranged so that the sum of every pair of adjacent elements is equal.
# Idea: If there is more than one distinct value, their frequencies must differ by at most 1; if there is only one distinct value, the array is always valid.

from collections import Counter

t = int(input())

while t > 0:
    n = int(input())
    a = list(map(int, input().split()))

    freq = Counter(a)
    Values = list(freq.values())

    if len(Values) > 2:
        print("NO")
    elif len(Values) == 1:
        print("YES")
    else:
        freq1 = Values[0]
        freq2 = Values[1]
        diff = abs(freq1 - freq2)

        if diff <= 1:
            print("YES")
        else:
            print("NO")

    t -= 1