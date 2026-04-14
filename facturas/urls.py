from django.urls import path
from . import views

urlpatterns = [
    path('previsualizar/', views.previsualizar_factura, name='previsualizar_factura'),
    path('generar/', views.generar_factura, name='generar_factura'),
]
