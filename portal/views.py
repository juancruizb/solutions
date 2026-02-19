from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'portal/solutionsportal.html')

def historico(request):
    return render(request, 'portal/historico.html')
