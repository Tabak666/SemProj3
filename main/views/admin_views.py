from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from ..models import Users, PasswordResetRequest, UserTablePairs

def approvals_view(request):
    if not request.session.get('user_id'):
        return redirect('login')
    if request.session.get('role') != 'admin':
        return redirect('index')

    pending_users = Users.objects.filter(approved=False)
    pending_password_resets = PasswordResetRequest.objects.filter(processed=False).select_related('user')
    approved_users_count = Users.objects.filter(approved=True).count()

    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        if request_type == 'user':
            user_id = request.POST.get('user_id')
            action = request.POST.get('action')
            try:
                user = Users.objects.get(id=user_id)
                if action == 'approve':
                    user.approved = True
                    user.save()
                    messages.success(request, f'{user.username} has been approved.')
                elif action == 'decline':
                    user.delete()
                    messages.warning(request, f'{user.username} has been declined and removed.')
            except Users.DoesNotExist:
                messages.error(request, "User not Found")
        elif request_type == 'password_reset':
            reset_id = request.POST.get('reset_id')
            action = request.POST.get('action')
            try:
                reset_request = PasswordResetRequest.objects.get(id=reset_id)
                user = reset_request.user
                if action == 'approve':
                    user.set_password(reset_request.new_password)
                    user.save()
                    reset_request.approved = True
                    reset_request.processed = True
                    reset_request.save()
                    messages.success(request, f'Password reset approved for {user.username}.')
                elif action == 'decline':
                    reset_request.processed = True
                    reset_request.save()
                    messages.warning(request, f'Password reset declined for {user.username}.')
            except PasswordResetRequest.DoesNotExist:
                messages.error(request, "Password reset request not found")
        return redirect('approvals')
    
    context = {
        'pending_users': pending_users,
        'pending_password_resets': pending_password_resets,
        'approved_users_count': approved_users_count
    }
    return render(request, 'approvals.html', context)

def admin_force_unpair(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"})
    if request.session.get("role") != "admin":
        return JsonResponse({"success": False, "message": "Not authorized"})
    desk_id = request.POST.get("desk_id")
    if not desk_id:
        return JsonResponse({"success": False, "message": "No desk selected"})
    UserTablePairs.objects.filter(desk_id=desk_id, end_time__isnull=True).update(end_time=timezone.now())
    return JsonResponse({"success": True, "message": f"Desk {desk_id} unpaired"})
