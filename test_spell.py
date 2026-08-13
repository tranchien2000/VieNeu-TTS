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
    print(f"Input:  {t}")
    print(f"Output: {result}")
    print()