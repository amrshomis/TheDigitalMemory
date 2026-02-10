from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import uuid

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
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('magazine_detail', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = "مجلة"
        verbose_name_plural = "المجلات"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
