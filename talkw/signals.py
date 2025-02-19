from django.db.models.signals import post_save
from django.dispatch import receiver
from talkw.models import Comment, Notification

@receiver(post_save, sender=Comment)
def notify_comment_reply(instance, created, **kwargs):
    """เมื่อมีคนตอบกลับคอมเมนต์ของผู้ใช้ ให้สร้าง Notification"""
    if created and instance.parent_comment:  # เช็คว่ามี parent_comment หรือไม่
        print("Creating Notification...")  # <-- Debugging จุดนี้
        Notification.objects.create(
            user=instance.parent_comment.author,  # เจ้าของคอมเมนต์ต้นฉบับ
            sender=instance.author,  # คนที่ตอบกลับ
            thread=instance.thread,  # กระทู้ที่เกี่ยวข้อง
            comment=instance,  # คอมเมนต์ที่ถูกสร้าง
            message=f"{instance.author.username} ตอบกลับคอมเมนต์ของคุณ",
        )
        print("Notification created!")  # <-- Debugging จุดนี้
