from rest_framework.routers import DefaultRouter
from django.urls import path
from jwt_auth import views


router = DefaultRouter()

router.register(prefix='jwt', viewset=views.AuthViewSet, basename='jwt')

urlpatterns = router.urls
