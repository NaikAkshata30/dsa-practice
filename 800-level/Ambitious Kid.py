# Codeforces: 1866A - Ambitious Kid
# Problem Description: Find the minimum number of operations needed to make the product of all array elements equal to zero.
# Idea: Making any one element zero is enough, so the minimum operations equals the smallest absolute value among all elements.

n = int(input())
a = list(map(int, input().split()))

min_num = abs(a[0])

for i in a:
    if abs(i) < min_num:
        min_num = abs(i)

print(min_num)