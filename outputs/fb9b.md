```python
from dataclasses import dataclass
from enum import Enum


class BmiCategory(Enum):
    UNDERWEIGHT = "U"
    NORMAL = "N"
    OVERWEIGHT = "O"
    OBESE = "OB"


@dataclass(frozen=True)
class BmiThreshold:
    upper: float
    category: BmiCategory


BMI_THRESHOLDS = [
    BmiThreshold(18.5, BmiCategory.UNDERWEIGHT),
    BmiThreshold(25.0, BmiCategory.NORMAL),
    BmiThreshold(30.0, BmiCategory.OVERWEIGHT),
]

RECOMMENDATIONS = {
    BmiCategory.NORMAL: "maintain",
    BmiCategory.OBESE: "consult doctor",
}


def classify_bmi(weight_kg: float, height_m: float) -> BmiCategory:
    bmi = weight_kg / height_m ** 2
    for threshold in BMI_THRESHOLDS:
        if bmi < threshold.upper:
            return threshold.category
    return BmiCategory.OBESE


def recommend(status: BmiCategory, age: int) -> str:
    if status in RECOMMENDATIONS:
        return RECOMMENDATIONS[status]

    if status == BmiCategory.UNDERWEIGHT:
        return "see pediatrician" if age < 18 else "gain weight"

    if status == BmiCategory.OVERWEIGHT:
        return "light exercise" if age > 60 else "exercise more"

    raise ValueError(f"Unhandled BMI category: {status}")
```
