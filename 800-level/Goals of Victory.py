# Codeforces: 1829A - Goals of Victory
# Problem Description: Given the efficiencies of n-1 teams in a tournament, determine the efficiency of the missing team.
# Idea: The sum of the efficiencies of all teams in the tournament is zero, so the missing efficiency is the negative of the sum of the given efficiencies.

t = int(input())

while t > 0:
    n = int(input())
    a = map(int, input().split())
    print(-sum(a))

    t -= 1