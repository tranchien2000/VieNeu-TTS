import os, sys, traceback
import importlib.util
module_path = os.path.abspath('src/vieneu_utils/chapter_detector.py')
spec = importlib.util.spec_from_file_location('chapter_detector', module_path)
chapter_detector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chapter_detector)
detect_chapters = chapter_detector.detect_chapters
_split_by_char_count = chapter_detector._split_by_char_count

def generate_text(length):
    chunk = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    text = ""
    i = 0
    while len(text) < length:
        text += chunk[i % len(chunk)]
        i += 1
        if i % 50 == 0:
            text += "\n"
    return text[:length]

def assert_equal(a,b,msg):
    if a!=b:
        raise AssertionError(f"{msg}: {a} != {b}")

# test _split_by_char_count
txt = generate_text(5500)
chapters = _split_by_char_count(txt, chars_per_chunk=2000)
assert_equal(len(chapters),3,'charcount parts')
reconstructed = "".join(c['text'] for c in chapters).replace('\n','')
assert_equal(reconstructed, txt.replace('\n',''), 'reconstruct text')

chapters = _split_by_char_count(txt, chars_per_chunk=2500)
assert_equal(len(chapters),3,'charcount 2500 parts')

# test detect_chapters charcount mode
chapters = detect_chapters(txt, format='auto', custom_keywords=None, words_per_chunk=1000, split_mode='charcount', chars_per_chunk=2000)
assert_equal(len(chapters),3,'detect charcount length')
assert_equal(chapters[0]['title'], 'Section 1','detect title 1')
assert_equal(chapters[-1]['title'], 'Section 3','detect title last')
assert_equal(chapters[-1]['end_pos'], len(txt), 'end pos')

# test detect_chapters wordcount mode
txt2 = "word " * 2500
chapters = detect_chapters(txt2, format='auto', custom_keywords=None, words_per_chunk=1000, split_mode='wordcount', chars_per_chunk=2000)
assert_equal(len(chapters),3,'wordcount parts')
assert all('Part' in c['title'] for c in chapters), 'title contains Part'
print('All checks passed')
