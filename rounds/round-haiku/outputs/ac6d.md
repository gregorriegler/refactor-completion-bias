```python
# BMI thresholds and classifications
BMI_THRESHOLDS = [
    (18.5, "U"),
    (25, "N"),
    (30, "O"),
    (float('inf'), "OB"),
]

# Recommendations by status and age
RECOMMENDATIONS = {
    "U": lambda age: "see pediatrician" if age < 18 else "gain weight",
    "N": lambda age: "maintain",
    "O": lambda age: "light exercise" if age > 60 else "exercise more",
    "OB": lambda age: "consult doctor",
}


def classify_bmi(weight_kg, height_m):
    """Classify BMI into categories: Underweight (U), Normal (N), Overweight (O), Obese (OB)."""
    bmi = weight_kg / (height_m ** 2)
    for threshold, category in BMI_THRESHOLDS:
        if bmi < threshold:
            return category


def recommend(status, age):
    """Get health recommendation based on BMI status and age."""
    recommendation_fn = RECOMMENDATIONS.get(status)
    return recommendation_fn(age) if recommendation_fn else None
```

Improvements made:
- Extracted magic numbers and strings into named constants at the module level
- Used data-driven lookup tables instead of repetitive if-elif chains
- Simplified logic using lambda functions for age-based recommendations
- Added docstrings for clarity
- Removed trailing blank lines
- Made the code more maintainable and testable
