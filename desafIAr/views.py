from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'desafIAr/home.html')

def video_form(request):
    return render(request, 'desafIAr/video_form.html')

def video_detail(request):
    return render(request, 'desafIAr/video_detail.html')