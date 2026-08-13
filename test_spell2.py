from src.vieneu_utils.vspell_checker import correct_text

tests = [
    "Toi di hoc o Ha Noi",
    "Hom nay troi dep qua",
    "Ban co muon an pho khong",
    "Toi ten la Nam",
    "Tieng Viet khong kho",
]

for t in tests:
    result = correct_text(t)
    # Write to file instead of printing
    with open("test_results.txt", "a", encoding="utf-8") as f:
        f.write(f"Input:  {t}\n")
        f.write(f"Output: {result}\n\n")

print("Done - check test_results.txt")