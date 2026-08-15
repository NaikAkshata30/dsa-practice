# Codeforces: 71A - Way Too Long Words
# Problem Description: Replace words longer than 10 characters with an abbreviation while keeping shorter words unchanged.
# Idea: For long words, keep the first and last characters and replace everything between them with the number of characters removed.

n = int(input())

for _ in range(n):
    s = input()

    if len(s) <= 10:
        print(s)
    else:
        print(s[0] + str(len(s) - 2) + s[-1])