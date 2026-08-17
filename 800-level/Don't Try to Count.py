# Codeforces: 1881A - Don't Try to Count
# Problem Description: Given strings x and s, determine the minimum number of operations needed to make s a substring of x.
# Idea: In each operation, append the current x to itself. Check whether s is a substring after each operation; at most 6 operations are needed because n * m <= 25.

t = int(input())

while t:
    n, m = map(int, input().split())
    x = input()
    s = input()

    operation = -1

    for ops in range(6):
        if s in x:
            operation = ops
            break
        x = x + x

    print(operation)
    t -= 1