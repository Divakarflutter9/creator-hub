from pathlib import Path
from django import forms
from .models import ResourceReport

MAX_UPLOAD_SIZE = 25 * 1024 * 1024
ALLOWED_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".zip", ".txt"}

class ResourceForm(forms.Form):
    title = forms.CharField(min_length=2, max_length=120)
    description = forms.CharField(max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 4, "maxlength": 1000}))
    article_body = forms.CharField(required=False, max_length=50000, widget=forms.Textarea(attrs={"rows": 18, "maxlength": 50000}))
    file = forms.FileField()
    visibility = forms.ChoiceField(choices=[("published", "Publish now — anyone with the link can view"), ("draft", "Save as draft — only visible to you")])

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("visibility") == "published" and not cleaned.get("article_body", "").strip():
            self.add_error("article_body", "Add your original article before publishing this resource.")
        return cleaned

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if not uploaded:
            return uploaded
        suffix = Path(uploaded.name).suffix.lower()
        if uploaded.size < 1 or uploaded.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError("Choose a file between 1 byte and 25 MB.")
        if suffix not in ALLOWED_TYPES:
            raise forms.ValidationError("Supported formats are PDF, PNG, JPG, ZIP, and TXT.")
        head = uploaded.read(16)
        uploaded.seek(0)
        signatures = {
            ".pdf": head.startswith(b"%PDF-"),
            ".png": head.startswith(b"\x89PNG\r\n\x1a\n"),
            ".jpg": head.startswith(b"\xff\xd8\xff"),
            ".jpeg": head.startswith(b"\xff\xd8\xff"),
            ".zip": head.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")),
            ".txt": b"\x00" not in head and not any(byte < 9 or 13 < byte < 32 for byte in head),
        }
        if not signatures[suffix]:
            raise forms.ValidationError("The file content does not match its extension.")
        return uploaded

class ResourceEditForm(ResourceForm):
    file = forms.FileField(required=False, label="Replace file (optional)")

class ResourceReportForm(forms.ModelForm):
    class Meta:
        model = ResourceReport
        fields = ["reason", "details"]
        widgets = {"details": forms.Textarea(attrs={"rows": 3, "maxlength": 1000})}
