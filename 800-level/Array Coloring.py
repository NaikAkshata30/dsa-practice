# Codeforces: 1857A - Array Coloring
# Problem Description: Determine whether the array can be divided into two non-empty groups
# such that the sums of both groups have the same parity.
# Idea: The total number of odd elements must be even. If it is odd, the two group
# sums will always have different parity.

t = int(input())

while t > 0:
    n = int(input())
    a = list(map(int, input().split()))

    sum_of_odd = 0

    for i in a:
        if i % 2 == 1:
            sum_of_odd += 1

    if sum_of_odd % 2 == 1:
        print("No")
    else:
        print("Yes")

    t -= 1