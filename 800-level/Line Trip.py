# Codeforces: 1901A - Line Trip
# Problem Description: Find the minimum fuel tank capacity needed to travel from 0 to x and return to 0, refueling at the given gas stations.
# Idea: Find the largest distance between consecutive stations, but double the distance from the last station to x because the car has to make the return trip.

t = int(input())

while t > 0:
    n, x = map(int, input().split())
    a = list(map(int, input().split()))

    ans = a[0]

    for i in range(1, n):
        ans = max(ans, a[i] - a[i - 1])

    ans = max(ans, 2 * (x - a[n - 1]))

    print(ans)

    t -= 1