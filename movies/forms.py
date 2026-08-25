from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = [
            "rating",
            "title",
            "body",
        ]

        widgets = {
            "rating": forms.Select(
                choices=[
                    (1, "1 - Poor"),
                    (2, "2 - Below Average"),
                    (3, "3 - Average"),
                    (4, "4 - Good"),
                    (5, "5 - Excellent"),
                ]
            ),

            "title": forms.TextInput(
                attrs={
                    "placeholder": "Review title"
                }
            ),

            "body": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Share your experience..."
                }
            ),
        }