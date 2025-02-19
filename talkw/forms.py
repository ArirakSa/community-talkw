from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from datetime import date
from django.db.models import QuerySet


class CustomUserCreationForm(UserCreationForm):
    birthdate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
        required=True
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username'}),
        required=True
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'birthdate', 'email', 'password1', 'password2']

    def clean_birthdate(self):
        birthdate = self.cleaned_data.get('birthdate')
        if not birthdate:
            raise forms.ValidationError("Birthdate is required.")

        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if age < 12:
            raise forms.ValidationError("You must be at least 12 years old to register.")

        return birthdate

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()  # ทำความสะอาดข้อมูลที่กรอก
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # ตรวจสอบว่ารหัสผ่านทั้งสองตรงกันหรือไม่
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match")  # ถ้ารหัสผ่านไม่ตรงกัน ให้แสดงข้อผิดพลาด

        return cleaned_data



class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'bio', 'profile_picture']

    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        required=True
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about yourself'}),
        required=False
    )
    profile_picture = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        required=False  # ไม่บังคับให้ต้องอัปโหลดรูป
    )







class ThreadForm(forms.ModelForm):
    hashtags = forms.CharField(
        required=False,
        help_text="ใส่ Hashtags คั่นด้วยเครื่องหมายจุลภาค เช่น #Django, #Python"
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'โปรดใส่เนื้อหา','style': 'width: 100%; height: 200px;'}),
        required=True
    )
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'โปรดใส่หัวข้อ','style': 'width: 100%; height: 30px;'}),
        required=True
    )

    class Meta:
        model = Thread
        fields = ["title", "content", "hashtags", "anonymous"]

    def clean_hashtags(self):
        """ แปลง hashtags ที่รับเข้ามาเป็น list """
        hashtags_text = self.cleaned_data.get("hashtags", "")
        hashtags_list = [
            tag.strip("#").strip() for tag in hashtags_text.split(",") if tag.strip()
        ]
        return hashtags_list

    def save(self, commit=True):
        """ บันทึก Hashtags พร้อมกับ Thread """
        thread = super().save(commit=False)  # บันทึก Thread ก่อน
        hashtags_list = self.cleaned_data["hashtags"]

        if commit:
            thread.save()  # ต้องบันทึก Thread ก่อนถึงจะเพิ่ม ManyToMany ได้
            for tag in hashtags_list:
                hashtag, created = Hashtag.objects.get_or_create(name=tag)  # ถ้าไม่มีให้สร้างใหม่
                thread.hashtags.add(hashtag)  # เพิ่ม hashtag เข้า Thread

        return thread

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

from django import forms
from .models import Slang, Article

class SlangForm(forms.ModelForm):
    class Meta:
        model = Slang
        fields = ['word', 'meaning', 'is_profane']


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'created_by']
