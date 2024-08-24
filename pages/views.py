from django.shortcuts import render, HttpResponse, redirect
from .models import ContactForm, Events
from django.views.decorators.http import require_POST
import datetime
from .forms import EventImageForm

def index(request):
    return render(request, 'index.html')

@require_POST
def adminEventsCreate(request):
    title = request.POST.get("eventName")
    description = request.POST.get("eventDescription")
    cost = int(request.POST.get("ticketCost"))
    date_str = request.POST.get("eventDate")
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    print(date)
    Events.objects.create(title = title, description = description, cost = cost, eventdate = date)
    return redirect("adminEvents")

def adminEvents(request):
    form = EventImageForm()
    events = Events.objects.all()
    return render(request, "portal/events.html", {"events":events, "form":form})

def about(request):
    return render(request, 'about.html')

def events(request):
    events = Events.objects.all()
    return render(request, 'events.html', {"events":events})

def sitemap(request):
    return HttpResponse(open('templates/sitemap.xml').read(), content_type='text/xml')

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        ContactForm.objects.create(name = name, email = email, message = message)
    return render(request, 'contact.html')

@require_POST
def add_image(request, event_id):
    event = Events.objects.get(id=event_id)
    if request.method == 'POST':
        form = EventImageForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('adminEvents')
    else:
        form = EventImageForm(instance=event)
    return render(request, 'your_template_name.html', {'form': form, 'event': event})

@require_POST
def change_event(request, event_id):
    event = Events.objects.get(id=event_id)
    event.status = False
    event.save()
    return redirect('adminEvents')