from django.db import models
import uuid

class ContactForm(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()

class Events(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    eventdate = models.DateField()
    cost = models.IntegerField()
    image = models.FileField(blank=True)
    status = models.BooleanField(default=True)
    def __str__(self):
        return self.title

class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Events, on_delete=models.CASCADE)
    purchaseDate = models.DateField(auto_now_add=True)
    email = models.EmailField()

class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tickets = models.ManyToManyField(Ticket, blank=True)
    email = models.EmailField()
    cost = models.IntegerField()
    verified = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)