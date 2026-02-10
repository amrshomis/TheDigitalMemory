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

        # Trigger Image Conversion
        self.convert_to_images()

    def convert_to_images(self):
        """
        Converts PDF pages to images for high-performance loading.
        """
        try:
            # Create output directory
            output_dir = os.path.join(settings.MEDIA_ROOT, 'magazines', 'pages', self.slug)
            os.makedirs(output_dir, exist_ok=True)
            
            # Check if pages already exist (skip if already converted)
            if self.pages.exists():
                return

            input_path = self.pdf_file.path
            output_pattern = os.path.join(output_dir, 'page_%03d.jpg')
            
            # Ghostscript command for PDF -> Images (JPEG)
            # -r150 = 150 DPI (Good balance)
            # -dJPEGQ=85 = High JPEG quality
            command = [
                'gs', '-sDEVICE=jpeg', 
                '-dTextAlphaBits=4', '-dGraphicsAlphaBits=4', 
                '-r150', '-dJPEGQ=85',
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-sOutputFile={output_pattern}',
                input_path
            ]
            
            subprocess.run(command, check=True)
            
            # Create MagazinePage objects
            # List all generated files
            files = sorted([f for f in os.listdir(output_dir) if f.startswith('page_') and f.endswith('.jpg')])
            
            for i, filename in enumerate(files, 1):
                # Construct relative path for ImageField
                relative_path = os.path.join('magazines', 'pages', self.slug, filename)
                
                MagazinePage.objects.create(
                    magazine=self,
                    page_number=i,
                    image=relative_path
                )
                
            print(f"Successfully converted {len(files)} pages for {self.slug}")

        except Exception as e:
            print(f"Image conversion failed: {e}")

class MagazinePage(models.Model):
    magazine = models.ForeignKey(Magazine, on_delete=models.CASCADE, related_name='pages')
    page_number = models.PositiveIntegerField()
    image = models.ImageField(upload_to='magazines/pages/')

    class Meta:
        ordering = ['page_number']
        verbose_name = "صفحة"
        verbose_name_plural = "صفحات المجلة"

    def __str__(self):
        return f"{self.magazine.title} - p{self.page_number}"

    def get_absolute_url(self):
        return reverse('magazine_detail', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = "مجلة"
        verbose_name_plural = "المجلات"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
