# Example 8: Magic numbers and strings

```python
def classify_bmi(weight_kg, height_m):
    bmi = weight_kg / (height_m * height_m)
    if bmi < 18.5:
        return "U"
    elif bmi < 25:
        return "N"
    elif bmi < 30:
        return "O"
    else:
        return "OB"

def recommend(status, age):
    if status == "U":
        if age < 18:
            return "see pediatrician"
        return "gain weight"
    elif status == "N":
        return "maintain"
    elif status == "O":
        if age > 60:
            return "light exercise"
        return "exercise more"
    elif status == "OB":
        return "consult doctor"
```
