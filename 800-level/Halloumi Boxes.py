# Codeforces: 1903A - Halloumi Boxes
# Problem Description: Determine whether the boxes can be sorted in non-decreasing order using reversals of length at most k.
# Idea: If k is greater than 1, the array can always be rearranged into sorted order; if k is 1, no changes are possible, so the array must already be sorted.

l = int(input())

for _ in range(l):
    n, k = map(int, input().split())
    arr = list(map(int, input().split()))

    if k == 1:
        if arr == sorted(arr):
            print("YES")
        else:
            print("NO")
    else:
        print("YES")