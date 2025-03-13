from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import *

urlpatterns = [
    path("", HomeView.as_view(), name="Not_login_home"),  # กำหนดหน้าแรก
    path("home/", HomeView.as_view(), name="home"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("signout/", SignOutView.as_view(), name="signout"),
    path("signin/", SignInView.as_view(), name="signin"),
    path("content/", ContentView.as_view(), name="content"),
    path('profile/', ProfileView.as_view(), name='profile'),  # ลิงก์ไปโปรไฟล์ของผู้ใช้
    path('profile/<int:pk>/', ProfileView.as_view(), name='profile_other'),  # โปรไฟล์ของผู้ใช้อื่น
    path('search/', SearchResultsView.as_view(), name='search_results'),
    path("notifications/", NotificationListView.as_view(), name="notifications_list"),
    # path('notifications/read/<int:notification_id>/', MarkNotificationAsReadView.as_view(), name='mark_as_read'),
    path("community/", CommunityView.as_view(), name="community"),
    path("profile/edit/", EditProfileView.as_view(), name="edit_profile"),

    # 🔹 Admin URLs
    path("admin-dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("user-management/", UserManagementView.as_view(), name="user_management"),
    path("content-management/", ContentManagementView.as_view(), name="content_management"),
    path("admin-signin/", AdminSignInView.as_view(), name="admin_signin"),
    path('admin/signout/', AdminSignOutView.as_view(), name='admin_signout'),
    path('admin/content/', views.ContentManagementView.as_view(), name='content_management'),
    path('admin/content/add-slang/', views.SlangCreateView.as_view(), name='add_slang'),
    path('admin/content/add-article/', views.ArticleCreateView.as_view(), name='add_article'),
    path('admin/content/add-badword/', views.BadWordCreateView.as_view(), name='add_badword'),
    path('admin/content/edit/<int:pk>/', views.ArticleUpdateView.as_view(), name='content_edit'),
    path('admin/content/delete/<int:pk>/', views.ArticleDeleteView.as_view(), name='article_delete'),
    # 🔹 Thread URLs
    path('comment/<int:thread_id>/', CommentCreateView.as_view(), name='comment_create'),
    path('thread/<int:thread_id>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('hashtag/<int:pk>/', views.HashtagDetailView.as_view(), name='hashtag_detail'),  # สำหรับหน้า Hashtag Detail
    path("threads-detail/<int:pk>/", ThreadDetailView.as_view(), name="thread_detail"),
    path("threads/", ThreadListView.as_view(), name="thread_list"),
    path("create/", ThreadCreateView.as_view(), name="thread_form"),
    path('thread/<int:pk>/edit/', ThreadUpdateView.as_view(), name='thread_edit'),
    path('thread/<int:pk>/delete/', ThreadDeleteView.as_view(), name='thread_delete'),
    path('thread/<int:pk>/report/', ReportThreadView.as_view(), name='thread_report'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
