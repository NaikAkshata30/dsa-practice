# Codeforces: 1837A - Grasshopper on a Line
# Problem Description: Find the minimum number of jumps needed to reach x,
# where every jump distance must not be divisible by k.
# Idea: If x is not divisible by k, one jump of x is enough.
# Otherwise, use two jumps: x - 1 and 1. Neither jump is divisible by k.

t = int(input())

while t > 0:
    x, k = map(int, input().split())

    if x % k == 0:
        print(2)
        print(x - 1, 1)
    else:
        print(1)
        print(x)

    t -= 1
