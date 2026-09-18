# Codeforces: 1853A - Desorting
# Problem Description: Find the minimum number of operations needed to make
# a sorted array become unsorted.
# Idea: The operation reduces the difference between adjacent elements by 2.
# Therefore, find the minimum adjacent difference and calculate how many
# operations are needed to make that difference negative.

t = int(input())

while t > 0:
    n = int(input())
    a = list(map(int, input().split()))

    for i in range(n - 1):
        if a[i] > a[i + 1]:
            print(0)
            break
    else:
        min_diff = float('inf')

        for i in range(n - 1):
            diff = a[i + 1] - a[i]
            if diff < min_diff:
                min_diff = diff

        min_number_of_ops = (min_diff // 2) + 1
        print(min_number_of_ops)

    t -= 1