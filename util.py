def ds(f):
    ans = f"${int(f * 100) / 100}"
    if "." not in ans:
        ans += "."
    while len(ans) < 3 or ans[-3] != ".":
        ans += "0"
    for spot in [6, 10]:
        if len(ans) > spot + 1:
            ans = ans[:-spot] + "," + ans[-spot:]
    return ans
