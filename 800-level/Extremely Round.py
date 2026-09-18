# Codeforces: 1766A - Extremely Round
# Problem Description: Count how many positive integers from 1 to n
# have exactly one non-zero digit.
# Idea: For a one-digit number, every number is extremely round.
# For larger numbers, the answer is (number of digits - 1) * 9
# plus the first digit.

t = int(input())

while t > 0:
    n = int(input())

    str_n = str(n)
    total_digit = len(str_n)
    first_n = str_n[0]

    if n < 10:
        print(n)
    else:
        x = (total_digit - 1) * 9
        total = x + int(first_n)
        print(total)

    t -= 1