from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .serializers import ChatMessageSerializer
from .models import Conversation, Message
import openai
from django.conf import settings

# Add OpenAI API key configuration
openai.api_key = settings.OPENAI_API_KEY

User = get_user_model()


class ChatGPTView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatMessageSerializer(data=request.data)

        if serializer.is_valid():
            user_message = serializer.validated_data['message']
            user_role = serializer.validated_data.get('role', 'user')
            conversation_id = request.data.get('conversation_id')  # Get conversation_id from request

            user = User.objects.get(id=request.user.id)

            print(f"User: {user}, Remaining tokens: {user.remaining_tokens}")

            if user.remaining_tokens <= 0:
                return Response({"error": "You are out of tokens."}, status=status.HTTP_403_FORBIDDEN)

            # If conversation_id is provided, try to get that specific conversation
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                    # Verify user has access to this conversation
                    if not conversation.messages.filter(user=user).exists():
                        return Response(
                            {"error": "You don't have access to this conversation"}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Conversation.DoesNotExist:
                    return Response(
                        {"error": f"Conversation {conversation_id} not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Create new conversation if no ID provided
                conversation = Conversation.objects.create(user_role=user_role)

            # Deduct token for this request
            user.remaining_tokens -= 1
            user.save()

            # Get conversation history
            previous_messages = conversation.messages.all().order_by('created_at')
            conversation_history = [
                {"role": msg.role, "content": msg.content} 
                for msg in previous_messages
            ]
            conversation_history.append({"role": "user", "content": user_message})

            # Create new message in the conversation
            Message.objects.create(
                conversation=conversation,
                content=user_message,
                role='user',
                user=user
            )

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=conversation_history,
                    max_tokens=100
                )
                chatbot_response = response['choices'][0]['message']['content'].strip()
                tokens_used = response['usage']['total_tokens']

                # Save AI response
                Message.objects.create(
                    conversation=conversation,
                    content=chatbot_response,
                    role='assistant',
                    tokens_used=tokens_used,
                    user=user
                )

                user.remaining_tokens -= tokens_used
                user.save()

                return Response({
                    "response": chatbot_response,
                    "remaining_tokens": user.remaining_tokens,
                    "conversation_id": conversation.id,
                    "message_history": [{
                        "role": msg["role"],
                        "content": msg["content"]
                    } for msg in conversation_history] + [
                        {"role": "assistant", "content": chatbot_response}
                    ]
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationHistoryView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id=None, *args, **kwargs):
        user = request.user
        
        if conversation_id:
            try:
                # Get specific conversation
                conversation = Conversation.objects.filter(
                    id=conversation_id,
                    messages__user=user
                ).distinct().first()
                
                if not conversation:
                    return Response(
                        {"error": "Conversation not found or unauthorized"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                messages = conversation.messages.all().order_by('created_at')
                message_data = [{
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at
                } for msg in messages]
                
                return Response({
                    "conversation_id": conversation.id,
                    "messages": message_data
                }, status=status.HTTP_200_OK)
                
            except Conversation.DoesNotExist:
                return Response({"error": "Conversation not found"}, 
                             status=status.HTTP_404_NOT_FOUND)
        else:
            # Get all conversations without duplicates
            conversations = (Conversation.objects
                           .filter(messages__user=user)
                           .distinct()
                           .order_by('-messages__created_at'))
            
            # Use a set to track processed conversation IDs
            seen_conversations = set()
            conversation_data = []
            
            for conv in conversations:
                if conv.id not in seen_conversations:
                    seen_conversations.add(conv.id)
                    # Get the latest message for this conversation
                    latest_message = conv.messages.latest('created_at')
                    first_message = conv.messages.earliest('created_at')
                    
                    conversation_data.append({
                        "conversation_id": conv.id,
                        "last_message": latest_message.content,
                        "created_at": first_message.created_at
                    })
            
            return Response({
                "conversations": conversation_data
            }, status=status.HTTP_200_OK)