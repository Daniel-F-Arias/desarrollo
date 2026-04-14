from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from django.contrib.auth.models import User

class CrearUsuarioForm(UserCreationForm):
    identificacion = forms.CharField(label="Número de identificación", max_length=20, required=True)
    email = forms.EmailField(label="Correo electrónico", required=True)

    class Meta:
        model = User
        fields = ['identificacion', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['identificacion']  # 👈 usamos identificación como username
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class AccionUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    accion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    detalle = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.accion} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"