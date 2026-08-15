# Codeforces: 339A - Helpful Maths
# Problem Description: Rearrange the numbers in a sum so that they are in non-decreasing order.
# Idea: Split the sum into individual numbers, sort them, and join them back together using '+'.

s = input()
l = s.split('+')
l.sort()
res = '+'.join(l)
print(res)