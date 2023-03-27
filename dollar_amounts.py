from util import ds

chunks = {
    "techcu": 70813.9,
    "earnest": 20000,
    "etrade_transfer_1": 42852.91,
    "etrade_transfer_2": 99085.49,
}

print(" +\n".join([f"{k}: {ds(v)}" for k, v in chunks.items()] + [""]))
print("-----------------------------------")
print(f"= Total: {ds(sum(chunks.values()))}")

chunks = {
    "techcu": 125732.76,
    "earnest": 20000,
    "tea_transfer": 50000,
    "etrade_transfer_2": 99085.49,
}

print(" +\n".join([f"{k}: {ds(v)}" for k, v in chunks.items()
print("-----------------------------------")
print(f"= Total: {ds(sum(chunks.values()))}")
