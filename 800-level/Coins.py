# Codeforces: 1814A - Coins
# Problem Description: Determine whether n can be represented using coins
# with denominations 2 and k.
# Idea: If n is even, it can be formed using only coins of value 2.
# Otherwise, when n is odd, k must be odd and n - k must be even.

t = int(input())

while t > 0:
    n, k = map(int, input().split())

    if n % 2 == 0 or (n - k) % 2 == 0:
        print("YES")
    else:
        print("NO")

    t -= 1