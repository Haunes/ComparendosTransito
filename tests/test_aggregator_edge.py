from aggregator import canonical_num, has_leading_letter

def test_canonical_num_edge_and_leading_letter():
    assert canonical_num("X12345678") == "12345678"
    assert canonical_num("abc") == "abc"         # < 8 dígitos → se respeta
    assert canonical_num("A00-01.23 4567") == "0001234567"
    assert has_leading_letter("D05001000000048513677") is True
    assert has_leading_letter("05001000000048513677") is False
