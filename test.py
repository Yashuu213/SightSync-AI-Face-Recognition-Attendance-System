def mara():
    arr = list(map(int, input().split()))

    fer = {}

    for i in arr:
        if i in fer:
            fer[i] += 1
        else:
            fer[i] = 1

    print(fer)

mara()