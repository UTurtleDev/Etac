from django import forms
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from .models import Cabinet, User


class CollaborateurInscriptionForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="Prénom")
    last_name = forms.CharField(max_length=150, required=True, label="Nom")
    email = forms.EmailField(required=True, label="Adresse email")
    cabinet = forms.ModelChoiceField(
        queryset=Cabinet.objects.all(),
        required=True,
        label="Cabinet",
        empty_label="Sélectionnez un cabinet",
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'cabinet', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.is_collaborateur = True
        if commit:
            user.save()
        return user


def inscription_collaborateur(request):
    if request.method == 'POST':
        form = CollaborateurInscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('collaborateur_login')
    else:
        form = CollaborateurInscriptionForm()
    return render(request, 'users/inscription.html', {'form': form})
