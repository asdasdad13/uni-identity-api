from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.views.generic.edit import CreateView
from .forms import StudentCreationForm
from django.urls import reverse_lazy

def index(request):
    return render(request, 'index.html')


class RegisterView(CreateView):
    template_name = 'register_student.html'
    form_class = StudentCreationForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        # Save user to database
        response = super().form_valid(form)
        # Log the user in immediately after registration
        login(self.request, self.object)

        return response