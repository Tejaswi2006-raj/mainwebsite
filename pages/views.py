from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import ContactForm, Events, Invoice, Ticket
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.auth.hashers import make_password, check_password
import barcode
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from barcode.writer import ImageWriter
from io import BytesIO
from django.conf import settings
import datetime
from .forms import EventImageForm
import random
from django.core.mail import send_mail
import stripe
from django.utils import timezone
from django.contrib import messages
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64

stripe.api_key = settings.STRIPE_SECRET_KEY
    
def verifyTicketSuccess(request, invoice_id, ticket_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if invoice.tickets.filter(id=ticket_id).exists():
        return render(request, 'portal/ticket_success.html', {'invoice': invoice, 'ticket_id': ticket_id})
    else:
        return redirect('verifyTicketFailure', invoice_id=invoice_id, ticket_id=ticket_id)

def verifyTicketFailure(request, invoice_id, ticket_id):
    return render(request, 'ticket_failure.html', {'invoice_id': invoice_id, 'ticket_id': ticket_id})

def generate_otp():
    return str(random.randint(100000, 999999))



def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('adminEvents')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def send_otp(email):
    otp = generate_otp()
    subject = 'Your Verification code'
    message = f'Your Verification code is: {otp}'
    send_mail(subject, message, 'your_email@example.com', [email])
    return otp

def buy_tickets(request, event_id):
    event = Events.objects.get(id=event_id)
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        number_of_tickets = int(request.POST.get('tickets'))
        otp = send_otp(email)
        request.session['otp'] = otp
        request.session['email'] = email
        request.session['first_name'] = first_name
        request.session['last_name'] = last_name
        request.session['event_id'] = str(event.id)
        request.session['number_of_tickets'] = number_of_tickets
        request.session['otp_timestamp'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        return redirect('verify_email')
    return render(request, 'buy_tickets.html', {'event': event})

def verify_email(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_expiry_time_str = request.session.get('otp_expiry_time')
        otp_expiry_time = None
        if otp_expiry_time_str:
            try:
                otp_expiry_time = timezone.datetime.fromisoformat(otp_expiry_time_str)
            except ValueError:
                otp_expiry_time = None
        if otp_expiry_time and timezone.now() > otp_expiry_time:
            messages.error(request, 'The OTP has expired.')
            return redirect('verify_email')
        if entered_otp == stored_otp:
            email = request.session.get('email')
            last_name = request.session.get('last_name')
            first_name = request.session.get('first_name')
            event_id = request.session.get('event_id')
            number_of_tickets = request.session.get('number_of_tickets')
            event = Events.objects.get(id=event_id)
            tickets = []
            cost = 0
            for _ in range(number_of_tickets):
                ticket = Ticket(event=event, purchaseDate=timezone.now(), email=email)
                ticket.save()
                tickets.append(ticket)
                cost+=event.cost
            invoice = Invoice(email=email, first_name = first_name, last_name = last_name, verified=True, cost = cost)
            invoice.save()
            invoice.tickets.set(tickets)
            invoice.save()
            request.session.pop('otp', None)
            request.session.pop('otp_expiry_time', None)
            request.session.pop('email', None)
            request.session.pop('event_id', None)
            request.session.pop('number_of_tickets', None)
            return redirect('payment_page', invoice.id)
        else:
            messages.error(request, 'Invalid OTP.')
            return redirect('verify_email')
    return render(request, 'verify_email.html')

def show_tickets(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = send_otp(email)
        request.session['otp'] = otp
        request.session['email'] = email
        request.session['otp_timestamp'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        return redirect('verify_tickets')    
    return render(request, 'show_tickets.html')

def verify_tickets(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_expiry_time_str = request.session.get('otp_expiry_time')
        otp_expiry_time = None
        if otp_expiry_time_str:
            try:
                otp_expiry_time = timezone.datetime.fromisoformat(otp_expiry_time_str)
            except ValueError:
                otp_expiry_time = None
        if otp_expiry_time and timezone.now() > otp_expiry_time:
            messages.error(request, 'The OTP has expired.')
            return redirect('verify_email')
        if entered_otp == stored_otp:
            email = request.session.get('email')
            invoice = Invoice.objects.filter(email=email, verified=True).order_by('-date').first()
            if not invoice:
                messages.error(request, 'No valid invoice found.')
                return redirect('verify_email')
            tickets = Ticket.objects.filter(invoice=invoice)
            barcodes = {}
            for ticket in tickets:
                barcode_data = str(ticket.id)
                barcode_obj = barcode.Code128(barcode_data, writer=ImageWriter())
                buffer = BytesIO()
                barcode_obj.write(buffer)
                barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                barcodes[ticket.id] = barcode_base64
            request.session.pop('otp', None)
            request.session.pop('otp_expiry_time', None)
            request.session.pop('email', None)
            context = {
                'invoice': invoice,
                'tickets': tickets,
                'barcodes': barcodes,
            }
            return render(request, 'ticketsDisplay.html', context)
        else:
            messages.error(request, 'Invalid OTP.')
            return redirect('verify_email')
    return render(request, 'verify_email.html')

def payment_page(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    total_amount = invoice.cost * 100  # Example: each ticket costs $10.00 (1000 cents)
    if request.method == 'POST':
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=total_amount,
                currency='usd',
                description=f'Payment for invoice {invoice_id}',
                metadata={'invoice_id': str(invoice_id)},
            )
            client_secret = payment_intent['client_secret']
            return render(request, 'payment_page.html', {
                'invoice': invoice,
                'total_amount': total_amount / 100,
                'stripe_publishable_key': 'pk_test_51MsYaVIj9JFN5Py8ttbhr1SvNPFQxIJs31AjnD7QJmbc0FbAahnkSjlvIENI4BSZJ4JRNBoBYdg0FeaGHeBN5ugG00NQfe7HzC',
                'client_secret': client_secret
            })
        except stripe.error.StripeError as e:
            return render(request, 'payment_error.html', {'error': str(e)})
    payment_intent = stripe.PaymentIntent.create(
        amount=total_amount,
        currency='usd',
        description=f'Payment for invoice {invoice_id}',
        metadata={'invoice_id': str(invoice_id)},
    )
    client_secret = payment_intent['client_secret']
    return render(request, 'payment_page.html', {
        'invoice': invoice,
        'total_amount': total_amount / 100,
        'stripe_publishable_key': 'pk_test_51MsYaVIj9JFN5Py8ttbhr1SvNPFQxIJs31AjnD7QJmbc0FbAahnkSjlvIENI4BSZJ4JRNBoBYdg0FeaGHeBN5ugG00NQfe7HzC',
        'client_secret': client_secret
    })

def payment_success(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    if invoice.verified:
        # Retrieve invoice items
        tickets = invoice.tickets.all()
        invoice_items = [
            {
                'name': ticket.event.title,
                'description': ticket.event.description,
                'quantity': 1,  # Assuming each ticket represents 1 quantity
                'unit_price': ticket.event.cost,
                'total': ticket.event.cost
            }
            for ticket in tickets
        ]
        total_amount = sum(item['total'] for item in invoice_items)

        # Render the email template with invoice details
        subject = 'Your Payment was Successful'
        message = render_to_string('invoice_email.html', {
            'customer_name': invoice.email,  # Assuming email is the customer's name
            'invoice_items': invoice_items,
            'total_amount': total_amount,
        })

        # Send email using Django's send_mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Replace with your email address
            [invoice.email],  # Replace with recipient's email address
            fail_silently=False,
            html_message=message,  # Include HTML content
        )

        # Redirect to a success page
        return render(request, 'payment_success.html', {'invoice': invoice})

def index(request):
    return render(request, 'index.html')

@require_POST
@login_required
def adminEventsCreate(request):
    title = request.POST.get("eventName")
    description = request.POST.get("eventDescription")
    cost = int(request.POST.get("ticketCost"))
    date_str = request.POST.get("eventDate")
    date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    Events.objects.create(title = title, description = description, cost = cost, eventdate = date)
    return redirect("adminEvents")

def reset(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST['new-password']
            password2 = request.POST['confirm-password']
            if password1 == password2:
                user.password = make_password(password1)
                user.save()
                return redirect('login')
        return render(request, 'portal/resetPassword.html')
    else:
        return redirect("forgotPassword")

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if User.objects.get(email = email):
            user = User.objects.get(email=email)
            current_site = get_current_site(request)
            subject = 'Reset Your Password'
            message = render_to_string('email/passwordReset.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http',
            })
            send_mail(subject, '', 'noreplycomputerconcepts@gmail.com', [user.email],  html_message=message)
            return redirect('login')
    return render(request, 'portal/forgotPassword.html')

@login_required
def adminEvents(request):
    form = EventImageForm()
    events = Events.objects.all()
    return render(request, "portal/events.html", {"events":events, "form":form})

def invoices(request, event_id):
    invoices = Invoice.objects.filter(tickets__event_id=event_id).distinct()
    return render(request, "portal/invoices.html", {"invoices":invoices})

def about(request):
    return render(request, 'about.html')

def email(request):
    return render(request, 'emailEnter.html')

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
    if event:
        event.status = False
        event.save()
    else:
        event.status = True
        event.save()
    return redirect('adminEvents')