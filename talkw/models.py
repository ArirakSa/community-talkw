from django.db import models
from datetime import date
from django.contrib.auth.models import AbstractUser, BaseUserManager
from tailwind.validate import ValidationError
from django.contrib.auth import get_user_model

class TimeStampedModel(models.Model):
    class Meta:
        abstract = True  # ทำให้ไม่สร้างตารางในฐานข้อมูล

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

class CustomUser(AbstractUser):

    first_name = None
    last_name = None

    BIRTHDATE_CHOICES = [
        ('teen', 'Teen (12-19)'),
        ('preadult', 'Preadult (20-29)'),
        ('adult', 'Adult (30-59)'),
        ('old', 'Old (60+)'),
        ('unknown', 'Unknown'),
    ]
    birthdate = models.DateField(blank=True, null=True)
    user_category = models.CharField(max_length=10, choices=BIRTHDATE_CHOICES, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)  # เก็บข้อมูล bio
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)  # ฟิลด์รูปโปรไฟล์
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('admin', 'Admin')], default='user')
    def save(self, *args, **kwargs):
        # คำนวณ user_category ใหม่ทุกครั้งที่บันทึก
        self.user_category = self.calculate_category(self.birthdate)
        if self.is_superuser:
            self.role = 'admin'
        super(CustomUser, self).save(*args, **kwargs)

    def calculate_category(self, birthdate):
        if not birthdate:  # ถ้า birthdate เป็น None ให้คืนค่า 'unknown'
            return 'unknown'

        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

        if 12 <= age <= 19:
            return 'teen'
        elif 20 <= age <= 29:
            return 'preadult'
        elif 30 <= age <= 59:
            return 'adult'
        elif age >= 60:
            return 'old'

        return 'unknown'


class Member(models.Model):
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE)
    membership_start = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Add logic here to insert into MySQL `members` table
        if not self.user.pk:
            self.user.save()  # Ensure CustomUser is saved before linking in Member model


class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

    def thread_count(self):
        # ฟังก์ชันนี้จะคืนค่าจำนวนครั้งที่ Hashtag นี้ถูกใช้ใน Thread
        return self.threads.count()




class Thread(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    hashtags = models.ManyToManyField('Hashtag', related_name="threads", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='threads')

    def save(self, *args, **kwargs):
        self.clean()  # เรียกตรวจสอบคำหยาบก่อนบันทึก
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ReportThread(models.Model):
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.reported_by} on {self.thread}"





class Comment(models.Model):
    thread = models.ForeignKey(Thread, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # ฟิลด์ parent_comment สำหรับการตอบกลับคอมเมนต์
    parent_comment = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )

    def __str__(self):
        return f"Comment by {self.author.username} on {self.thread.title}"



class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_notifications")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:20]}"

    class Meta:
        ordering = ["-created_at"]  # เรียงตามเวลาล่าสุดก่อน

        # ✅ เมธอดสำหรับอัปเดตสถานะการอ่าน

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

class BadWord(models.Model):
    word = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.word






class Slang(models.Model):
    word = models.CharField(max_length=255, unique=True)
    meaning = models.TextField()
    is_profane = models.BooleanField(default=False)  # ถ้าคำนี้เป็นคำหยาบ
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.word

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

    @property
    def creator_name(self):
        return self.created_by.username if self.created_by else "Unknown"