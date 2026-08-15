# Codeforces: 1899A - Game with Integers
# Problem Description: Determine which player wins based on whether the given integer is divisible by 3 after Vanya's optimal move.
# Idea: If n is divisible by 3, any move makes it non-divisible; otherwise, Vanya can always add or subtract 1 to make it divisible by 3.

t = int(input())

while t > 0:
    n = int(input())

    if n % 3 == 0:
        print("Second")
    else:
        print("First")

    t -= 1