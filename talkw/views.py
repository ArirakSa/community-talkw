from datetime import timezone

from django.contrib.auth.views import *
from django.core.checks import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import *
from .forms import *
from .models import *
from django.db.models import Count
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.db.models import Q
from django.urls import reverse
import re
from django.http import JsonResponse
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import ReportThread, Thread
from django.contrib import messages


# -------------------------
# 🔹 Home Page (CBV)
# -------------------------
class HomeView(ListView):
    model = Thread
    template_name = "home.html"
    context_object_name = 'threads'  # กำหนดชื่อ context ที่จะใช้ในเทมเพลต

    def get_queryset(self):
        # กรอง Thread ตาม Hashtag หากมี
        hashtag_name = self.kwargs.get('hashtag_name', None)
        if hashtag_name:
            return Thread.objects.filter(hashtags__name=hashtag_name).order_by('-created_at')
        return Thread.objects.all().order_by('-created_at')


class ContentView(TemplateView):
    template_name = "content.html"
# -------------------------
# 🔹 Authentication Views (CBV)
# -------------------------
class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'signup.html'
    success_url = reverse_lazy('signin')

class SignInView(LoginView):
    template_name = "signin.html"

    def get_success_url(self):
        next_url = self.request.GET.get("next")

        if self.request.user.is_authenticated:  # ตรวจสอบว่าผู้ใช้ล็อคอินแล้ว
            if self.request.user.role == 'user':
                if next_url:
                    return next_url
                else:
                    return reverse_lazy('home')
            else:
                messages.error(self.request, "กรุณาล็อคอินด้วยบัญชีผู้ใช้ที่สมัครสมาชิก")
                return reverse_lazy('signin')
        else:
            messages.error(self.request, "กรุณาล็อคอินก่อนเข้าสู่ระบบ")
            return reverse_lazy('signin')

class AdminSignInView(LoginView):
    template_name = "admin/admin_signin.html"

    def get_success_url(self):
        next_url = self.request.GET.get("next")

        if self.request.user.is_authenticated:  # ตรวจสอบว่าผู้ใช้ล็อคอินแล้ว
            if self.request.user.role == 'admin':
                if next_url:
                    return next_url
                else:
                    return reverse_lazy('admin_dashboard')
            else:
                messages.error(self.request, "กรุณาล็อคอินด้วยบัญชีแอดมิน")
                return reverse_lazy('signin')
        else:
            messages.error(self.request, "กรุณาล็อคอินก่อนเข้าสู่ระบบ")
            return reverse_lazy('signin')


class SignOutView(LogoutView):
    print("ออกแล้ววว")
    next_page = reverse_lazy('signin')

class AdminSignOutView(LogoutView):
    next_page = reverse_lazy('admin_signin')

# -------------------------
# 🔹 Profile Views (CBV)
# -------------------------
class ProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = "profile.html"
    context_object_name = 'profile_user'

    def get_object(self, **kwargs):
        # ถ้า `pk` ถูกส่งมาใน URL (สำหรับโปรไฟล์ผู้ใช้อื่น)
        if self.kwargs.get('pk'):
            return get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        else:
            # ถ้าไม่มี `pk` แสดงว่าเป็นโปรไฟล์ของผู้ที่ล็อกอินอยู่
            return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # เพิ่ม threads ของผู้ใช้เข้าไปใน context
        context['threads'] = self.get_object().threads.all()
        return context




@method_decorator(login_required, name="dispatch")
class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = EditProfileForm(instance=request.user)
        return render(request, "edit_profile.html", {"form": form})

    def post(self, request):
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
        return render(request, "edit_profile.html", {"form": form})

# -------------------------
# 🔹 Thread Views (CBV)
# -------------------------



class SearchResultsView(ListView):
    model = Thread
    template_name = 'thread/search_results.html'
    context_object_name = 'threads'  # ตัวแปรที่ใช้ใน template

    def get_queryset(self):
        query = self.request.GET.get('q', '')  # รับค่าจาก query parameter 'q'
        if query:
            # ค้นหาจาก title, content และ hashtags ของ Thread
            return Thread.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(hashtags__name__icontains=query)  # ค้นหาจากชื่อของ hashtags
            ).distinct()  # ใช้ distinct เพื่อหลีกเลี่ยงผลลัพธ์ซ้ำ
        return Thread.objects.none()  # หากไม่มีคำค้นหาจะไม่แสดงอะไร


# ฟังก์ชันตรวจสอบคำหยาบ
def check_bad_words(content):
    bad_words = BadWord.objects.values_list('word', flat=True)  # ดึงคำหยาบจากฐานข้อมูล
    for bad_word in bad_words:
        if bad_word in content:
            return True  # ถ้าพบคำหยาบ ให้คืนค่า True
    return False

class ThreadCreateView(LoginRequiredMixin, CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'thread/thread_form.html'
    success_url = reverse_lazy('home')  # กลับหน้า home หลังจากโพสต์เสร็จ

    def form_valid(self, form):
        # กำหนด author ของกระทู้
        form.instance.author = self.request.user

        # ดึง content จากฟอร์ม
        content = form.cleaned_data.get('content', '')

        if content:
            # ตรวจสอบคำหยาบในเนื้อหาของกระทู้
            if check_bad_words(content):
                # หากพบคำหยาบ ให้เพิ่ม error และไม่ให้บันทึกกระทู้
                form.add_error('content', 'กระทู้นี้มีคำหยาบโปรดแก้ไข')
                return self.form_invalid(form)

            # ใช้ regex ดึง Hashtags
            hashtags = set(re.findall(r'#(\w+)', content))  # ใช้ # แล้วตามด้วยคำที่ไม่มีช่องว่าง

            # บันทึกกระทู้
            thread = form.save()

            # เชื่อมโยง hashtags ที่พบในเนื้อหาของกระทู้
            for hashtag in hashtags:
                clean_hashtag = hashtag.lower()  # แปลงเป็นตัวพิมพ์เล็กเพื่อป้องกันซ้ำ
                hashtag_obj, created = Hashtag.objects.get_or_create(name=clean_hashtag)
                thread.hashtags.add(hashtag_obj)

        return super().form_valid(form)





class ThreadCreateView2(LoginRequiredMixin, CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'thread/thread_form.html'
    success_url = reverse_lazy('home')  # กลับหน้า home หลังจากโพสต์เสร็จ

    def form_valid(self, form):
        # กำหนด author ของกระทู้
        form.instance.author = self.request.user

        # ดึง content จากฟอร์ม
        content = form.cleaned_data.get('content', '')

        if content:
            # ตรวจสอบคำหยาบในเนื้อหาของกระทู้
            if check_bad_words(content):
                # หากพบคำหยาบ ให้เพิ่ม error และไม่ให้บันทึกกระทู้
                form.add_error('content', 'กระทู้นี้มีคำหยาบโปรดแก้ไข')
                return self.form_invalid(form)

            # ใช้ regex ดึง Hashtags
            hashtags = set(re.findall(r'#+(\w+)', content))

            # บันทึกกระทู้
            thread = form.save()

            # เชื่อมโยง hashtags ที่พบในเนื้อหาของกระทู้
            for hashtag in hashtags:
                clean_hashtag = hashtag.lower()  # แปลงเป็นตัวพิมพ์เล็กเพื่อป้องกันซ้ำ
                hashtag_obj, created = Hashtag.objects.get_or_create(name=clean_hashtag)
                thread.hashtags.add(hashtag_obj)

        return super().form_valid(form)


class ThreadCreateView1(LoginRequiredMixin, CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'thread/thread_form.html'
    success_url = reverse_lazy('home')  # กลับหน้า home หลังจากโพสต์เสร็จ

    def form_valid(self, form):
        # กำหนด author ของกระทู้
        form.instance.author = self.request.user

        # ดึงเนื้อหาของกระทู้
        content = form.cleaned_data.get('content', '')

        # ดึงคำหยาบทั้งหมดจากฐานข้อมูล (สมมติว่า model BannedWord มี field 'word')
        banned_words = list(BannedWord.objects.values_list('word', flat=True))

        # ตรวจสอบว่ามีคำหยาบอยู่ในเนื้อหาหรือไม่
        for banned in banned_words:
            # ใช้ re.escape เพื่อหลีกเลี่ยง special characters ใน banned word
            pattern = re.compile(re.escape(banned), re.IGNORECASE)
            if pattern.search(content):
                form.add_error('content', f'เนื้อหาของคุณมีคำที่ไม่เหมาะสม: "{banned}" ไม่อนุญาตให้ใช้')
                return self.form_invalid(form)

        # ดึง Hashtags จากเนื้อหา โดยใช้ regex (ค้นหาคำที่ขึ้นต้นด้วย '#' ตามด้วยตัวอักษรหรือตัวเลข)
        hashtags = set(re.findall(r'#+(\w+)', content))

        # บันทึกกระทู้
        thread = form.save()

        # เชื่อมโยง Hashtags ที่พบในเนื้อหาของกระทู้
        for hashtag in hashtags:
            clean_hashtag = hashtag.lower()  # แปลงเป็นตัวพิมพ์เล็กเพื่อป้องกันซ้ำ
            hashtag_obj, created = Hashtag.objects.get_or_create(name=clean_hashtag)
            thread.hashtags.add(hashtag_obj)

        return super().form_valid(form)


class ThreadListView(ListView):
    model = Thread
    template_name = 'thread/thread_list.html'
    context_object_name = 'threads'  # กำหนดชื่อ context ที่จะใช้ในเทมเพลต

    def get_queryset(self):
        # กรอง Thread ตาม Hashtag หากมี
        hashtag_name = self.kwargs.get('hashtag_name', None)
        if hashtag_name:
            return Thread.objects.filter(hashtags__name=hashtag_name).order_by('-created_at')
        return Thread.objects.all().order_by('-created_at')



class ThreadDetailView(DetailView):
    model = Thread
    template_name = "thread/thread_detail.html"
    context_object_name = 'thread'

    def get(self, request, *args, **kwargs):
        thread = self.get_object()

        # ✅ อัปเดตแจ้งเตือนที่เกี่ยวข้องกับโพสต์นี้ให้เป็น "อ่านแล้ว"
        if request.user.is_authenticated:
            Notification.objects.filter(user=request.user, thread=thread, is_read=False).update(is_read=True)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_object()

        # ค้นหา Threads ที่มี Hashtags เหมือนกัน
        hashtags = thread.hashtags.all()
        hashtag_ids = [hashtag.id for hashtag in hashtags]

        # ค้นหาคอมเมนต์ที่เกี่ยวข้อง
        comments = Comment.objects.filter(thread=thread)

        # ค้นหา threads ที่มี hashtag เหมือนกับ thread นี้
        similar_threads = Thread.objects.filter(
            hashtags__in=hashtag_ids
        ).exclude(id=thread.id)  # เอา thread ที่ดูอยู่แล้วออกจากผลลัพธ์

        # ค้นหา threads ที่เนื้อหาคล้ายกัน (ค้นหาคำบางคำจาก content)
        query = Q(content__icontains=thread.title) | Q(content__icontains=thread.content[:100])  # ตัวอย่างการค้นหาคล้ายกัน
        content_similar_threads = Thread.objects.filter(query).exclude(id=thread.id)

        # รวมทั้งสองกรณี
        combined_threads = similar_threads | content_similar_threads

        # คำแสลง
        slangs = Slang.objects.all()
        content = thread.content  # เนื้อหาของโพสต์
        slang_info = []

        # แทนที่คำแสลงในเนื้อหาของโพสต์ด้วย HTML ที่มี tooltip
        for slang in slangs:
            if slang.word in content:
                replacement = (
                    f'<span class="group relative text-blue-500  cursor-pointer">'
                    f'{slang.word}'
                    f'<span class="absolute left-1/2 -translate-x-1/2 bottom-full mb-4 px-4 py-2 text-base text-white bg-black rounded opacity-0 group-hover:opacity-100 transition duration-300 whitespace-nowrap">'
                    f'{slang.meaning}'
                    f'</span>'
                    f'</span>'
                )
                content = content.replace(slang.word, replacement)
                slang_info.append({'word': slang.word, 'meaning': slang.meaning})


        # ส่งค่าไปยัง context
        context['slang_info'] = slang_info
        context['threads'] = combined_threads.distinct()
        context['comments'] = comments
        context['content'] = mark_safe(content)
        return context


class CommunityView(ListView):
    model = Thread
    template_name = 'community.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ดึง popular hashtags ที่มีการใช้งานใน threads โดยจัดเรียงตามจำนวน threads ที่เกี่ยวข้อง
        context['popular_hashtags'] = Hashtag.objects.annotate(
            thread_count=Count('threads')
        ).order_by('-thread_count')[:20]  # เอา 20 อันดับแฮชแท็กที่ใช้บ่อย

        return context


class HashtagDetailView(LoginRequiredMixin, DetailView):
    model = Hashtag
    template_name = 'hashtag_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hashtag = self.get_object()
        context['threads'] = hashtag.threads.all()  # หรือคำสั่งอื่นๆ ขึ้นอยู่กับว่าอยากแสดงอะไร
        return context



class ThreadUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'thread/thread_form.html'

    def test_func(self):
        thread = self.get_object()
        return self.request.user == thread.author

    def get_success_url(self):
        return reverse_lazy('profile')


class ThreadDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Thread
    success_url = reverse_lazy('profile')

    def test_func(self):
        thread = self.get_object()
        return self.request.user == thread.author

    def post(self, request, *args, **kwargs):
        thread = self.get_object()
        thread.delete()
        return JsonResponse({"success": True})

class ReportThreadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        thread = Thread.objects.get(pk=pk)
        reason = request.POST.get("reason", "").strip()
        image = request.FILES.get("image")

        if not reason and not image:
            return JsonResponse({"success": False, "error": "Please provide a reason or attach an image."}, status=400)

        report = ReportThread.objects.create(thread=thread, user=request.user, reason=reason)

        if image:
            file_path = f"reports/{thread.id}/{image.name}"
            default_storage.save(file_path, ContentFile(image.read()))
            report.image = file_path
            report.save()

        return JsonResponse({"success": True})






class CommentCreateView1(LoginRequiredMixin, View):
    def post(self, request, thread_id):
        content = request.POST.get("content", "").strip()
        if not content:
            return JsonResponse({"success": False, "error": "Comment cannot be empty."}, status=400)

        thread = Thread.objects.get(pk=thread_id)
        comment = Comment.objects.create(
            thread=thread,
            content=content,
            author=request.user
        )

        return JsonResponse({"success": True})



class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, thread_id):
        # รับข้อมูลคอมเมนต์จาก request
        content = request.POST.get('content', '').strip()

        # ถ้า content ว่างหรือไม่ถูกต้อง
        if not content:
            return JsonResponse({"success": False, "error": "Comment cannot be empty."}, status=400)

        # ค้นหากระทู้
        thread = get_object_or_404(Thread, pk=thread_id)

        # สร้าง comment ใหม่
        comment = Comment.objects.create(
            thread=thread,
            content=content,
            author=request.user
        )

        # แจ้งเตือนเฉพาะกรณีที่เจ้าของกระทู้ไม่ใช่คนที่คอมเมนต์
        if request.user != thread.author:
            notification_message = f'{request.user.username} commented on your thread: "{thread.title}"'
            Notification.objects.create(
                sender=request.user,
                user=thread.author,  # เจ้าของกระทู้
                message=notification_message,
                thread=thread,
                is_read=False
            )

        # ตอบกลับด้วย JsonResponse
        return JsonResponse({"success": True, "message": "Comment added successfully."})


class NotificationListView1(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications.html"
    context_object_name = "notifications"

    def get_queryset(self):
        # ฟิลเตอร์ข้อมูลให้แสดงเฉพาะ notification ของผู้ใช้ที่ล็อกอินอยู่
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")



# สร้าง Notification ใหม่
class CreateNotificationView(LoginRequiredMixin, View):
    def post(self, request, thread_id):
        thread = Thread.objects.get(id=thread_id)  # ดึง thread จาก id
        user = request.user  # ผู้ใช้ที่ล็อกอิน
        message = request.POST['message']  # ข้อความคอมเมนต์ที่ผู้ใช้กรอก

        # สร้าง comment ใหม่
        comment = Comment.objects.create(
            thread=thread,
            user=user,
            message=message,
            created_at=timezone.now()
        )

        # สร้าง Notification สำหรับผู้ที่เป็นเจ้าของ thread
        notification = Notification.objects.create(
            sender=user,
            user=thread.user,  # ผู้ที่เป็นเจ้าของกระทู้
            message=f'{user.username} commented on your thread: {message}',
            thread=thread,
            is_read=False,
        )
        return JsonResponse({'success': True, 'message': 'Notification sent and comment added.'})


# View สำหรับการ Mark Notification เป็นอ่าน
class MarkNotificationAsReadView(LoginRequiredMixin, View):
    def post(self, request, notification_id):
        try:
            # ดึง Notification ตาม id และ user
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False}, status=404)


# แสดงรายการแจ้งเตือน
class NotificationListView1(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications.html"
    context_object_name = "notifications"

    def get_queryset(self):
        # ฟิลเตอร์ข้อมูลให้แสดงเฉพาะ notification ของผู้ใช้ที่ล็อกอินอยู่
        notifications = Notification.objects.filter(user=self.request.user).order_by("-created_at")
        return notifications

    def get_context_data(self, **kwargs):
        # เพิ่มการนับจำนวน notification ที่ยังไม่ได้อ่าน
        context = super().get_context_data(**kwargs)
        unread_notifications_count = Notification.objects.filter(user=self.request.user, is_read=False).count()
        context['unread_notifications_count'] = unread_notifications_count
        return context


class NotificationListView2(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications.html"
    context_object_name = "notifications"

    def get_queryset(self):
        # ฟิลเตอร์ข้อมูลให้แสดงเฉพาะ notification ของผู้ใช้ที่ล็อกอินอยู่
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # การนับจำนวน notification ที่ยังไม่ได้อ่าน
        unread_notifications_count = Notification.objects.filter(user=self.request.user, is_read=False).count()
        context['unread_notifications_count'] = unread_notifications_count

        # อัปเดตสถานะ notification เป็นอ่านแล้ว (is_read = True) เมื่อเข้ามาที่หน้า
        Notification.objects.filter(user=self.request.user, is_read=False).update(is_read=True)

        return context

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications.html"
    context_object_name = "notifications"

    def get_queryset(self):
        # ฟิลเตอร์ข้อมูลให้แสดงเฉพาะ notification ของผู้ใช้ที่ล็อกอินอยู่
        notifications = Notification.objects.filter(user=self.request.user).order_by("-created_at")
        return notifications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # นับจำนวน notifications ที่ยังไม่ได้อ่าน
        unread_notifications_count = Notification.objects.filter(user=self.request.user, is_read=False).count()
        context['unread_notifications_count'] = unread_notifications_count
        return context

# -------------------------
# 🔹 Admin Views (CBV)
# -------------------------

class AdminDashboardView(TemplateView):
    template_name = "admin/admin_dashboard.html"


class UserManagementView(TemplateView):
    template_name = "admin/user_management.html"


class ContentManagementView(TemplateView):
    template_name = "admin/content_management.html"


from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from .models import Slang, Article
from .forms import SlangForm, ArticleForm

# สร้างคำศัพท์หยาบและคำแสลง
class SlangCreateView(CreateView):
    model = Slang
    form_class = SlangForm
    template_name = 'admin/add_slang.html'
    success_url = reverse_lazy('content_management')  # หลังจากเพิ่มเสร็จจะไปที่หน้า Content Management

# สร้างบทความ
class ArticleCreateView(CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'admin/add_article.html'
    success_url = reverse_lazy('content_management')  # หลังจากเพิ่มเสร็จจะไปที่หน้า Content Management

# แสดงบทความทั้งหมด
class ContentManagementView(ListView):
    model = Article
    template_name = 'admin/content_management.html'
    context_object_name = 'contents'


from django.views.generic import UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Article

# แก้ไขบทความ
class ArticleUpdateView(UpdateView):
    model = Article
    fields = ['title', 'content', 'created_by']
    template_name = 'admin/edit_article.html'
    success_url = reverse_lazy('content_management')

# ลบบทความ
class ArticleDeleteView(DeleteView):
    model = Article
    template_name = 'admin/confirm_delete.html'
    success_url = reverse_lazy('content_management')
