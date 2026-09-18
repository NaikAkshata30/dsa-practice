# Codeforces: 1777A - Everybody Likes Good Arrays!
# Problem Description: Find the minimum number of operations required to make
# an array good, where every pair of adjacent elements has different parity.
# Idea: Every adjacent pair with the same parity requires one operation.
# Multiplying two numbers with the same parity produces an element of the same parity,
# so each such pair can be merged in one operation.

t = int(input())

while t > 0:
    n = int(input())
    a = list(map(int, input().split()))

    ops = 0

    for i in range(n - 1):
        if (a[i] % 2 == 0 and a[i + 1] % 2 == 0) or \
           (a[i] % 2 == 1 and a[i + 1] % 2 == 1):
            ops += 1

    print(ops)

    t -= 1