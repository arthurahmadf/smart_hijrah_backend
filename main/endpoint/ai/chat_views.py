from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from main.models_ai import ChatConversation, ChatMessage
from main.serializers.ai_serializers import ChatConversationSerializer
from main.gemini_client import get_islamic_response
import json
import time

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """Send message to AI and get response"""
    print(f"\n[VIEW] ========== SEND MESSAGE START ==========")
    view_start = time.time()
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', None)
        
        print(f"[VIEW] User: {request.user.username}")
        print(f"[VIEW] Message: {message[:50]}...")
        print(f"[VIEW] Conversation ID from request: {conversation_id}")
        
        if not message:
            return JsonResponse({
                "success": False,
                "message": "Message is required"
            }, status=400)
        
        # Get or create conversation
        conv_start = time.time()
        if conversation_id:
            print(f"[VIEW] Fetching existing conversation: {conversation_id}")
            conversation = get_object_or_404(ChatConversation, id=conversation_id, user=request.user)
            is_first = conversation.messages.count() == 0
            print(f"[VIEW] Existing conversation, is_first: {is_first}, message count: {conversation.messages.count()}")
        else:
            print(f"[VIEW] Creating new conversation")
            conversation = ChatConversation.objects.create(
                user=request.user,
                title=message[:50]
            )
            is_first = True
            print(f"[VIEW] New conversation created with ID: {conversation.id}")
        conv_time = time.time() - conv_start
        print(f"[VIEW] Conversation fetch/create time: {conv_time:.3f}s")
        
        # Save user message
        save_start = time.time()
        user_msg = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            text=message
        )
        save_time = time.time() - save_start
        print(f"[VIEW] Save user message time: {save_time:.3f}s")
        
        # Get chat history for context (last 5 messages only for efficiency)
        history_start = time.time()
        history = []
        for msg in conversation.messages.all().order_by('created_at')[:10]:
            history.append({
                "role": msg.role,
                "parts": [msg.text]
            })
        history_time = time.time() - history_start
        print(f"[VIEW] History fetch time: {history_time:.3f}s, history length: {len(history)}")
        
        # Get AI response
        ai_start = time.time()
        print(f"[VIEW] Calling Gemini API...")
        ai_response = get_islamic_response(
            message, 
            conversation_id=conversation.id,
            is_first_message=is_first
        )
        ai_time = time.time() - ai_start
        print(f"[VIEW] Gemini API total time (including session): {ai_time:.3f}s")
        
        # Save AI response
        save_ai_start = time.time()
        assistant_msg = ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            text=ai_response
        )
        save_ai_time = time.time() - save_ai_start
        print(f"[VIEW] Save AI message time: {save_ai_time:.3f}s")
        
        total_time = time.time() - view_start
        print(f"[VIEW] ========== TOTAL VIEW TIME: {total_time:.3f}s ==========\n")
        
        return JsonResponse({
            "success": True,
            "conversation_id": conversation.id,
            "is_first_message": is_first,
            "user_message": {
                "id": user_msg.id,
                "text": user_msg.text,
                "created_at": user_msg.created_at
            },
            "assistant_message": {
                "id": assistant_msg.id,
                "text": assistant_msg.text,
                "created_at": assistant_msg.created_at
            }
        }, status=200)
        
    except Exception as e:
        total_time = time.time() - view_start
        print(f"[VIEW] ERROR: {e}")
        print(f"[VIEW] Total time before error: {total_time:.3f}s")
        print(f"[VIEW] ========== END ==========\n")
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """Get all conversations for current user"""
    try:
        conv_start = time.time()
        conversations = ChatConversation.objects.filter(user=request.user)
        serializer = ChatConversationSerializer(conversations, many=True)
        elapsed = time.time() - conv_start
        print(f"[VIEW] Get conversations time: {elapsed:.3f}s")
        
        return JsonResponse({
            "success": True,
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_detail(request, conversation_id):
    """Get detailed conversation with all messages"""
    try:
        conv_start = time.time()
        conversation = get_object_or_404(ChatConversation, id=conversation_id, user=request.user)
        serializer = ChatConversationSerializer(conversation)
        elapsed = time.time() - conv_start
        print(f"[VIEW] Get conversation detail time: {elapsed:.3f}s")
        
        return JsonResponse({
            "success": True,
            "data": serializer.data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    try:
        conversation = get_object_or_404(ChatConversation, id=conversation_id, user=request.user)
        
        # Hapus chat session dari cache jika ada
        from main.gemini_client import chat_sessions
        if conversation.id in chat_sessions:
            del chat_sessions[conversation.id]
        
        conversation.delete()
        
        return JsonResponse({
            "success": True,
            "message": "Conversation deleted"
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)