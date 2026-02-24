from vieneu_utils.normalize_text import VietnameseTTSNormalizer
from vieneu_utils.core_utils import split_text_into_chunks

normalizer = VietnameseTTSNormalizer()
text = "Đoạn 1.\nĐoạn 2.\nĐoạn 3."
text2 = "chỉ số là 7,05 - đường huyết là 1.8 - bạn test trường hợp này"

print(f"Original text 1: {repr(text)}")
normalized_text = normalizer.normalize(text)
print(f"Normalized text 1: {repr(normalized_text)}")
print(f"Newlines in original: {text.count('\\n')}, Newlines in normalized: {normalized_text.count('\\n')}")

print(f"\nOriginal text 2: {repr(text2)}")
normalized_text2 = normalizer.normalize(text2)
print(f"Normalized text 2: {repr(normalized_text2)}")

chunks = split_text_into_chunks(normalized_text, max_chars=100)
print(f"\nChunks after normalization (should be 3):")
for i, c in enumerate(chunks):
    print(f"  Chunk {i+1}: {repr(c)}")

# If we split before normalizing (or if normalize kept newlines)
chunks_direct = split_text_into_chunks(text, max_chars=100)
print(f"\nExpected chunks (from original text):")
for i, c in enumerate(chunks_direct):
    print(f"  Chunk {i+1}: {repr(c)}")
