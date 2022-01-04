from django.contrib import admin
from django.urls import path
from board import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.list),
    path('write/', views.write),
    path('insert/', views.insert),
    path('detail/', views.detail),
    path('update/', views.update),
    path('delete/', views.delete),
    path('download/', views.download),
    path('reply_insert/', views.reply_insert),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)