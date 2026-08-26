# Codeforces: A. Buttons
# Problem Description: Determine whether Anna or Katie wins a game where each player
# can press their own buttons and both can press the shared buttons.
# Idea: If the number of shared buttons is odd, Anna gets the extra turn from them.
# Compare the remaining exclusive buttons to determine the winner.

t = int(input())

while t > 0:
    a, b, c = map(int, input().split())

    if c % 2 != 0:    #odd... katie's turn next
        if b > a:
            print("Second")
        else:
            print("First")
    else:
        if a > b:
            print("First")
        else:
            print("Second")

    t -= 1