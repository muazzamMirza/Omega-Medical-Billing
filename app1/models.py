from django.db import models

class UploadedPDF(models.Model):
    file = models.FileField(upload_to="uploaded_pdfs/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class ProcessedPage(models.Model):
    phone_number = models.CharField(max_length=20)  # (XXX)XXX-XXXX format
    pdf_file = models.FileField(upload_to="processed_pdfs/")  # Extracted page
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.pdf_file.name}"
