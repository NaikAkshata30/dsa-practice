# Codeforces: 1859A - United We Stand
# Problem Description: Split the array into two non-empty arrays such that
# no element of the second array divides any element of the first array.
# Idea: Put all maximum elements into one array and all remaining elements
# into the other. If all elements are equal, a valid split is impossible.

t = int(input())

while t > 0:
    n = int(input())
    a = list(map(int, input().split()))

    b = []
    c = []

    mx = max(a)
    mn = min(a)

    if mx == mn:
        print(-1)
        t -= 1
        continue

    for x in a:
        if x == mx:
            c.append(x)
        else:
            b.append(x)

    print(len(b), len(c))
    print(*b)
    print(*c)

    t -= 1