# Codeforces: 1873C - Target Practice
# Problem Description: Calculate the total score of all arrows placed on a 10x10 target, where each ring has a value from 1 to 5.
# Idea: Represent the target using a predefined 10x10 scoring grid and add the corresponding value for every cell containing "X".

t = int(input())

while t > 0:

    val = 0

    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
        [1, 2, 3, 3, 3, 3, 3, 3, 2, 1],
        [1, 2, 3, 4, 4, 4, 4, 3, 2, 1],
        [1, 2, 3, 4, 5, 5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5, 5, 4, 3, 2, 1],
        [1, 2, 3, 4, 4, 4, 4, 3, 2, 1],
        [1, 2, 3, 3, 3, 3, 3, 3, 2, 1],
        [1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]

    for i in range(10):
        a = input()

        for j in range(10):
            if a[j] == "X":
                val += grid[i][j]

    print(val)
    t -= 1