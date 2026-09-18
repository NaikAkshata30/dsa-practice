# Codeforces: 1845A - Forbidden Integer
# Problem Description: Determine whether n can be represented using integers from 1 to k,
# excluding x, and print any valid representation if possible.
# Idea: If x is not 1, use n copies of 1. If x is 1, use 2s when n is even,
# or one 3 and the remaining 2s when n is odd. A solution is impossible when
# only 2 is available and n is odd, or when k = 1.

t = int(input())

while t > 0:
    n, k, x = map(int, input().split())

    if x != 1:
        print("YES")
        print(n)
        print(*[1] * n)
    else:
        if k == 1 or k == 2 and n % 2 == 1:
            print("NO")
        else:
            if n % 2 == 0:
                print("YES")
                print(n // 2)
                print(*[2] * (n // 2))
            else:
                print("YES")
                print(((n - 3) // 2) + 1)
                print(3, *[2] * ((n - 3) // 2))

    t -= 1