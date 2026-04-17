```python
from enum import Enum


class BMICategory(Enum):
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE = "obese"


def classify_bmi(weight_kg: float, height_m: float) -> BMICategory:
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        return BMICategory.UNDERWEIGHT
    elif bmi < 25:
        return BMICategory.NORMAL
    elif bmi < 30:
        return BMICategory.OVERWEIGHT
    else:
        return BMICategory.OBESE


def recommend(category: BMICategory, age: int) -> str:
    if category is BMICategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"
    if category is BMICategory.NORMAL:
        return "maintain"
    if category is BMICategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"
    if category is BMICategory.OBESE:
        return "consult doctor"
    raise ValueError(f"Unhandled BMI category: {category}")
```
