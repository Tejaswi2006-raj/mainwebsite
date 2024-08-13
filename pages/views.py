from django.shortcuts import render, HttpResponse
from .models import ContactForm

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def sitemap(request):
    return HttpResponse(open('templates/sitemap.xml').read(), content_type='text/xml')

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        ContactForm.objects.create(name = name, email = email, message = message)
    return render(request, 'contact.html')