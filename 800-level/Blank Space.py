# Codeforces: 1829B - Blank Space
# Problem Description: Find the longest contiguous segment of zeroes in the array.
# Idea: Track the current zero run and retain the largest run seen.

t = int(input())

while t > 0:
    n = int(input())
    a = list(map(int, input().split()))
    cnt = 0
    max_cnt = 0
    
    for i in a:
        if i == 0:
            cnt += 1
            max_cnt = max(max_cnt, cnt)
        else:
            cnt = 0
    
    print(max_cnt)
            
    t -= 1
        
