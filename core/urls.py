# myapp/urls.py
from django.urls import path
from .views import ChatGPTView, ConversationHistoryView

urlpatterns = [
    path('chat/', ChatGPTView.as_view(), name='chat-gpt'),
    path('conversation/<int:conversation_id>/', ConversationHistoryView.as_view(), name='conversation-detail'),
    path('conversations/', ConversationHistoryView.as_view(), name='conversations'),
    ]
