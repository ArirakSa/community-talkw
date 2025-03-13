from datetime import timezone
from django.contrib.auth.views import *
from django.core.checks import messages
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.generic import *
from .forms import *
from .models import *
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
import re, json
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages



#  Home Page (CBV)
class HomeView(ListView):
    model = Thread
    template_name = "home.html"
    context_object_name = 'threads'  # กำหนดชื่อ context ที่จะใช้ในเทมเพลต

    def get_queryset(self):
        return Thread.objects.all().order_by('-created_at')

class ContentView(TemplateView):
    template_name = "content.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ดึงบทความทั้งหมดหรือบทความที่คุณต้องการแสดง
        context['articles'] = Article.objects.all()  # หรือจะใช้ filter หากต้องการเลือกบทความเฉพาะ
        return context
# -------------------------
#  Authentication Views (CBV)

class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'signup.html'
    success_url = reverse_lazy('signin')

class SignInView(LoginView):
    template_name = "signin.html"
    def form_invalid(self, form):
        messages.error(self.request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        return super().form_invalid(form)
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

class SignOutView(LogoutView):
    next_page = reverse_lazy('signin')


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
        context['threads'] = self.get_object().threads.all().order_by('-created_at')
        return context


@method_decorator(login_required, name="dispatch")
class EditProfileView(View):
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
#  Thread Views (CBV)

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
            hashtags = set(re.findall(r'#([\wก-๙]+)', content, re.UNICODE))
            # บันทึกกระทู้
            thread = form.save()

            # เชื่อมโยง hashtags ที่พบในเนื้อหาของกระทู้
            for hashtag in hashtags:
                clean_hashtag = hashtag.lower()  # แปลงเป็นตัวพิมพ์เล็กเพื่อป้องกันซ้ำ
                hashtag_obj, created = Hashtag.objects.get_or_create(name=clean_hashtag())
                thread.hashtags.add(hashtag_obj)

        # ดึงค่าจาก next parameter ถ้ามี
        next_url = self.request.GET.get('next', reverse_lazy('home'))

        # Redirect ไปยัง URL ที่เก็บใน next หรือ fallback ไปที่หน้า home
        return HttpResponseRedirect(next_url)


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

        #อัปเดตแจ้งเตือนที่เกี่ยวข้องกับโพสต์นี้ให้เป็น "อ่านแล้ว"
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
        ).filter(thread_count__gt=0).order_by('-thread_count')[:20]  # เอา 20 อันดับแฮชแท็กที่ใช้บ่อย

        return context


class HashtagDetailView(DetailView):
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
        # ตรวจสอบว่าเป็นเจ้าของกระทู้หรือไม่
        thread = self.get_object()
        return self.request.user == thread.author

    def form_valid(self, form):

        # ดึง content จากฟอร์ม
        content = form.cleaned_data.get('content', '')

        if content:
            # ตรวจสอบคำหยาบในเนื้อหาของกระทู้
            if check_bad_words(content):
                # หากพบคำหยาบ ให้เพิ่ม error และไม่ให้บันทึกกระทู้
                form.add_error('content', 'กระทู้นี้มีคำหยาบโปรดแก้ไข')
                return self.form_invalid(form)

            # ใช้ regex ดึง Hashtags
            hashtags = set(re.findall(r'#([\wก-๙]+)', content, re.UNICODE))
            # บันทึกกระทู้
            thread = form.save()

            # เชื่อมโยง hashtags ที่พบในเนื้อหาของกระทู้
            for hashtag in hashtags:
                clean_hashtag = hashtag.lower()  # แปลงเป็นตัวพิมพ์เล็กเพื่อป้องกันซ้ำ
                hashtag_obj, created = Hashtag.objects.get_or_create(name=clean_hashtag())
                thread.hashtags.add(hashtag_obj)

        # ดึงค่าจาก next parameter ถ้ามี
        next_url = self.request.GET.get('next', reverse_lazy('home'))

        # Redirect ไปยัง URL ที่เก็บใน next หรือ fallback ไปที่หน้า home
        return HttpResponseRedirect(next_url)


class ThreadDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Thread

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



class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, thread_id):
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({"success": False, "error": "Comment cannot be empty."}, status=400)

        if check_bad_words(content):
            return JsonResponse({"success": False, "error": "มีคำหยาบ โปรดทำการแก้ไข"}, status=400)

        thread = get_object_or_404(Thread, pk=thread_id)
        comment = Comment.objects.create(thread=thread, content=content, author=request.user)

        # แจ้งเตือนเฉพาะเจ้าของกระทู้
        if request.user != thread.author:
            Notification.objects.create(
                sender=request.user,
                user=thread.author,
                message=f'{request.user.username} commented on your thread: "{thread.title}"',
                thread=thread
            )

        return JsonResponse({
            "success": True,
            "message": "Comment added successfully.",
            "comment": {
                "author": comment.author.username,
                "content": comment.content,
                "created_at": comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })



# View สำหรับการ Mark Notification เป็นอ่าน
# class MarkNotificationAsReadView(LoginRequiredMixin, View):
#     def post(self, request, notification_id):
#         try:
#             # ดึง Notification ตาม id และ user
#             notification = Notification.objects.get(id=notification_id, user=request.user)
#             notification.is_read = True
#             notification.save(update_fields=['is_read'])
#             return JsonResponse({'success': True})
#         except Notification.DoesNotExist:
#             return JsonResponse({'success': False}, status=404)


# แสดงรายการแจ้งเตือน
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
#  Admin Views (CBV)

class AdminSignInView(LoginView):
    template_name = "admin/admin_signin.html"

    def get_success_url(self):
        next_url = self.request.GET.get("next")

        if self.request.user.is_authenticated:  # ตรวจสอบว่าผู้ใช้ล็อคอินแล้ว
            if self.request.user.role == 'admin': # ตรวจสอบว่าผู้ใช้เป็น admin
                if next_url:
                    return next_url # หากมี next_url ให้ไปที่หน้า next_url
                else:
                    return reverse_lazy('admin_dashboard') # รีไดเรกต์ไปที่ Admin Dashboard
            else:
                messages.error(self.request, "กรุณาล็อคอินด้วยบัญชีแอดมิน")
                return reverse_lazy('admin_signin')
        else:
            messages.error(self.request, "กรุณาล็อคอินก่อนเข้าสู่ระบบ")
            return reverse_lazy('admin_signin')


class AdminSignOutView(LogoutView):
    next_page = reverse_lazy('admin_signin')


from django.db.models import Count
from collections import Counter
import json

class AdminDashboardView1(LoginRequiredMixin, TemplateView):
    template_name = "admin/admin_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
            return redirect('home')  # เปลี่ยนไปหน้าที่ต้องการ
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user categories count
        user_categories_count = list(CustomUser.objects.filter(role='user')
                                     .values('user_category')
                                     .annotate(count=models.Count('user_category'))
                                     .order_by('user_category'))
        context['user_categories'] = json.dumps(user_categories_count)

        # Get total users
        context['total_users'] = CustomUser.objects.filter(role='user').count()

        # Get total content (articles)
        context['total_content'] = Article.objects.count()

        # Get total number of posts (articles)
        context['total_posts'] = Article.objects.count()

        # Get top 7 most used hashtags
        hashtags = Hashtag.objects.values('name').annotate(tag_count=Count('name')).order_by('-tag_count')[:7]
        context['top_hashtags'] = json.dumps(list(hashtags))

        return context

from django.contrib.auth.mixins import PermissionRequiredMixin

class AdminDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "admin/admin_dashboard.html"
    permission_required = "is_admin"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_categories_count = (
            CustomUser.objects.filter(role='user')
            .values('user_category')
            .annotate(count=models.Count('user_category'))
            .order_by('user_category')
        )
        context['user_categories'] = json.dumps(list(user_categories_count))

        context.update({
            'total_users': CustomUser.objects.filter(role='user').count(),
            'total_content': Article.objects.count(),
            'total_posts': Article.objects.count(),
            'top_hashtags': json.dumps(list(
                Hashtag.objects.values('name')
                .annotate(tag_count=Count('name'))
                .order_by('-tag_count')[:7]
            )),
        })
        return context


class UserManagementView(LoginRequiredMixin, TemplateView):
    template_name = "admin/user_management.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class ContentManagementView(LoginRequiredMixin, TemplateView):
    template_name = "admin/content_management.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        slang_contents = Slang.objects.all()
        article_contents = Article.objects.all()
        contents = list(slang_contents) + list(article_contents)

        context = super().get_context_data(**kwargs)
        context['contents'] = contents
        return context


# สร้างคำศัพท์หยาบและคำแสลง
class SlangCreateView(LoginRequiredMixin, CreateView):
    model = Slang
    form_class = SlangForm
    template_name = 'admin/add_slang.html'
    success_url = reverse_lazy('content_management')  # หลังจากเพิ่มเสร็จจะไปที่หน้า Content Management

class BadWordCreateView(LoginRequiredMixin, FormView):
    template_name = "admin/add_badword.html"
    form_class = BadwordForm
    success_url = reverse_lazy("content_management")

    def form_valid(self, form):
        words = form.cleaned_data["badwords"]
        added_words = []

        for word in words:
            obj, created = BadWord.objects.get_or_create(word=word)
            if created:
                added_words.append(word)

        if added_words:
            messages.success(self.request, f"เพิ่มคำใหม่เรียบร้อย: {', '.join(added_words)}")
        else:
            messages.info(self.request, "ไม่มีคำใหม่ถูกเพิ่ม เพราะมีอยู่แล้วในระบบ")

        return super().form_valid(form)



# สร้างบทความ
class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'admin/add_article.html'
    success_url = reverse_lazy('content_management')  # หลังจากเพิ่มเสร็จจะไปที่หน้า Content Management

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user  # กำหนด created_by เป็นผู้ใช้ที่ล็อกอิน
        else:
            return redirect('admin_signin')  # หากไม่ได้ล็อกอิน ให้ไปที่หน้าเข้าสู่ระบบ
        return super().form_valid(form)

# แสดงบทความทั้งหมด
# class ContentListView(LoginRequiredMixin, ListView):
#     model = Article
#     template_name = 'content.html'
#     context_object_name = 'contents'  # กำหนดชื่อ context ให้ตรงกับในเทมเพลต
#
#     def form_valid(self, form):
#         # ตรวจสอบว่า user ที่ล็อกอินมี role เป็น 'admin'
#         if self.request.user.role == 'admin':
#             # ตั้งค่าผู้สร้างเป็น user ที่ล็อกอิน
#             form.instance.created_by = self.request.user
#             return super().form_valid(form)
#         else:
#             # ถ้า user ไม่ใช่ admin แสดง error หรือทำอย่างอื่นตามต้องการ
#             form.add_error(None, 'You must be an admin to create an article.')
#             return self.form_invalid(form)

# แก้ไขบทความ
class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'admin/edit_article.html'
    success_url = reverse_lazy('content_management')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, "คุณไม่มีสิทธิ์แก้ไขบทความ")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
# ลบบทความ
class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    def post(self, request, pk):
        if not request.user.is_authenticated or request.user.role != "admin":
            return JsonResponse({'message': 'คุณไม่มีสิทธิ์ลบบทความ'}, status=403)

        try:
            content = Article.objects.get(id=pk)
            content.delete()
            return JsonResponse({'message': 'Content deleted successfully'}, status=200)
        except Article.DoesNotExist:
            return JsonResponse({'message': 'Content not found'}, status=404)
