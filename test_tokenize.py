from underthesea import word_tokenize

tests = [
    "Tôi đi học ở Hà Nội",
    "Hôm nay trời đẹp quá",
    "Bạn có muốn ăn phở không",
    "Tôi tên là Nam",
    "Tiếng Việt không khó"
]

with open("tokenize_results.txt", "w", encoding="utf-8") as f:
    for t in tests:
        result = word_tokenize(t, format="text")
        f.write(f"{t} -> {result}\n")

print("Done")