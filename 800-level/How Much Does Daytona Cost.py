# Codeforces: 1696A - How Much Does Daytona Cost?
# Problem Description: Determine whether there exists a non-empty subsegment where k is the most common element.
# Idea: A single occurrence of k forms a subsegment where k is the most common element, so it is enough to check whether k exists in the array.

t = int(input())

while t > 0:
    n, k = map(int, input().split())
    a = list(map(int, input().split()))

    if a.count(k) >= 1:
        print("YES")
    else:
        print("NO")

    t -= 1