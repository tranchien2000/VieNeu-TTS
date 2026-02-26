import pytest
from vieneu_utils.normalize_text import VietnameseTTSNormalizer

@pytest.fixture
def normalizer():
    return VietnameseTTSNormalizer()

@pytest.mark.parametrize("input_text, expected", [
    # 1. Số thông thường
    ("0", "không"),
    ("1", "một"),
    ("10", "mười"),
    ("11", "mười một"),
    ("21", "hai mươi mốt"),
    ("100", "một trăm"),
    ("1000", "một nghìn"),
    ("1001", "một nghìn không trăm lẻ một"),
    ("1000000", "một triệu"),
    ("1234567", "một triệu hai trăm ba mươi bốn nghìn năm trăm sáu mươi bảy"),

    # 2. Số thập phân
    ("1.000", "một nghìn"),
    ("1.000.000", "một triệu"),
    ("3,14", "ba phẩy mười bốn"),
    ("1.3", "một chấm ba"),

    # 3. Số điện thoại
    ("0912345678", "không chín một hai ba bốn năm sáu bảy tám"),
    ("+84912345678", "cộng tám bốn chín một hai ba bốn năm sáu bảy tám"),

    # 4. Số thứ tự đặc biệt
    ("thứ 1", "thứ nhất"),
    ("thứ 4", "thứ tư"),
    ("thứ 5", "thứ năm"),
    ("hạng 1", "hạng nhất"),

    # 5. Phép nhân
    ("3 x 4", "ba nhân bốn"),
    ("10 x 20", "mười nhân hai mươi"),

    # 6. Ngày tháng năm
    ("21/02/2025", "ngày hai mươi mốt tháng hai năm hai nghìn không trăm hai mươi lăm"),
    ("01-01-2024", "ngày một tháng một năm hai nghìn không trăm hai mươi bốn"),
    ("31.12.2023", "ngày ba mươi mốt tháng mười hai năm hai nghìn không trăm hai mươi ba"),
    ("21/02", "ngày hai mươi mốt tháng hai"),
    ("02/2025", "tháng hai năm hai nghìn không trăm hai mươi lăm"),
    ("32/01", "ba mươi hai không một"),

    # 7. Thời gian
    ("14h30", "mười bốn giờ ba mươi phút"),
    ("8h05", "tám giờ không năm phút"),
    ("23:59", "hai mươi ba giờ năm mươi chín phút"),
    ("12:00:00", "mười hai giờ không phút không giây"),

    # 8. Tiền tệ
    ("100$", "một trăm đô la Mỹ"),
    ("$50", "năm mươi đô la Mỹ"),
    ("500 VND", "năm trăm đồng"),
    ("1000đ", "một nghìn đồng"),
    ("75%", "bảy mươi lăm phần trăm"),

    # 9. Đơn vị đo lường
    ("50km", "năm mươi ki lô mét"),
    ("100m", "một trăm mét"),
    ("75kg", "bảy mươi lăm ki lô gam"),
    ("2l", "hai lít"),

    # 10. Số La Mã
    ("Thế kỷ XXI", "thế kỷ hai mươi mốt"),
    ("Chương IV", "chương bốn"),

    # 11. Chữ cái
    ("chữ B", "chữ bê"),
    ("ký tự 'C'", "ký tự xê"),

    # 12. Viết tắt
    ("UBND", "uỷ ban nhân dân"),
    ("TP.HCM", "thành phố hồ chí minh"),
    ("CSGT", "cảnh sát giao thông"),
    ("v.v", "vân vân"),

    # 13. EN Tag
    ("<en>Hello</en>", "<en>Hello</en>"),
    ("Xin chào <en>Good morning</en>", "xin chào <en>Good morning</en>"),
    
    # 14. Dấu câu
    ("A & B", "a và bê"),
    ("A + B", "a cộng bê"),
    
    # 15. Hỗn hợp
    ("Ngày 21/02/2025 lúc 14h30 tại TPHCM",
     "ngày hai mươi mốt tháng hai năm hai nghìn không trăm hai mươi lăm lúc mười bốn giờ ba mươi phút tại thành phố hồ chí minh"),
])
def test_normalize(normalizer, input_text, expected):
    actual = normalizer.normalize(input_text)
    # Clean up whitespace for comparison
    actual_clean = " ".join(actual.split()).lower()
    expected_clean = " ".join(expected.split()).lower()
    assert actual_clean == expected_clean
