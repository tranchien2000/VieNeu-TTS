from sea_g2p import Normalizer
n = Normalizer()
tests = [
    'toi di hoc o ha noi',
    'hom nay troi dep qua',
    'ban co muon an pho khong',
    'toi ten la nam',
    'tieng viet khong kho',
    '100 ng trieu dong',
    'ngay 20/10/2024'
]
with open("normalize_results.txt", "w", encoding="utf-8") as f:
    for t in tests:
        result = n.normalize(t)
        f.write(f"{t} -> {result}\n")
print("Done")