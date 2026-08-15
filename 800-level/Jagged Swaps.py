# Codeforces: 1896A - Jagged Swaps
# Problem Description: Determine whether a given permutation can be sorted using the allowed swapping operation.
# Idea: The permutation can be sorted only if 1 is already at the first position.

t = int(input())

while t > 0:
    n = int(input())
    a = list(map(int, input().split()))

    if a[0] == 1:
        print("YES")
    else:
        print("NO")

    t -= 1