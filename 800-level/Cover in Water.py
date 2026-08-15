# Codeforces: 1900A - Cover in Water
# Problem Description: Find the minimum number of actions needed to fill all empty cells with water.
# Idea: If there are three consecutive empty cells, only 2 initial water placements are needed; otherwise, every empty cell needs one placement.

t = int(input())

while t > 0:
    n = int(input())
    s = input()

    if "..." in s:
        print(2)
    else:
        print(s.count("."))

    t -= 1