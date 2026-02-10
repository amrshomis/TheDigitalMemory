from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import uuid
import os
import subprocess
from django.conf import settings

class Magazine(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان المجلة")
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name="رابط فريد")
    pdf_file = models.FileField(upload_to='magazines/pdfs/', verbose_name="ملف PDF")
    cover_image = models.ImageField(upload_to='magazines/covers/', blank=True, null=True, verbose_name="صورة الغلاف")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    def save(self, *args, **kwargs):
        if not self.slug:
            # Create a unique slug using title and a short uuid
            base_slug = slugify(self.title)
            if not base_slug: # handle non-latin characters
                base_slug = "magazine"
            self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        
        # Save first to ensure file exists on disk
        super().save(*args, **kwargs)

        # Post-save compression (only if file exists)
        if self.pdf_file:
            try:
                file_path = self.pdf_file.path
                if os.path.exists(file_path):
                    self.compress_pdf(file_path)
            except Exception as e:
                print(f"Compression skipped: {e}")

    def compress_pdf(self, input_path):
        """
        Attempts to compress PDF using Ghostscript (available on PythonAnywhere).
        """
        output_path = f"{input_path}_compressed.pdf"
        try:
            # Ghostscript command for ebook quality (150 dpi) - good balance
            # use 'screen' for 72dpi (lowest quality, smallest size)
            # use 'ebook' for 150dpi (medium quality)
            quality = '/ebook' 
            
            command = [
                'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS={quality}',
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-sOutputFile={output_path}',
                input_path
            ]
            
            subprocess.run(command, check=True)
            
            # If successful, replace original
            if os.path.exists(output_path):
                os.replace(output_path, input_path)
                print(f"Successfully compressed {input_path}")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            # GS not installed or failed - ignore
            if os.path.exists(output_path):
                os.remove(output_path)

    def get_absolute_url(self):
        return reverse('magazine_detail', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = "مجلة"
        verbose_name_plural = "المجلات"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
