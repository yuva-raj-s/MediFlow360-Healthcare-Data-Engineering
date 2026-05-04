# Unit Test Cases

```python
def test_strip_bom():
    assert strip_bom("\ufeffOrderID") == "OrderID"

def test_mask_phone():
    assert mask_phone_logic("9841012345") == "XXXXXX2345"

def test_fraud_score_F2():
    assert calculate_f2(250000) == 2
    assert calculate_f2(50000) == 0
```