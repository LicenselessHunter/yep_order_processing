from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required #Se importa el decorator.
from products.models import product

def home(request):
	return render(request, "home.html")
