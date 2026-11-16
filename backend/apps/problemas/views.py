
from rest_framework import viewsets

from .models import Problema
from .serializers import ProblemaSerializer


class ProblemaViewSet(viewsets.ModelViewSet):

    queryset = Problema.objects.all()
    serializer_class = ProblemaSerializer
