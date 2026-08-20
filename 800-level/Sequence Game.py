# Codeforces: 1862B - Sequence Game
# Problem Description: Given the resulting sequence b, construct any possible original sequence a that could produce b according to the game's rules.
# Idea: Start with the first element of b. Whenever the current element is smaller than the previous element, insert the current element twice; otherwise, append it once.

t = int(input())

while t > 0:
    n = int(input())
    b = list(map(int, input().split()))

    a = [b[0]]

    for i in range(1, n):
        if b[i] < b[i - 1]:
            a.append(b[i])
            a.append(b[i])
        else:
            a.append(b[i])

    print(len(a))
    print(*a)

    t -= 1