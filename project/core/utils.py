from django.contrib.admin.models import LogEntry, CHANGE, DELETION


def log_admin_action(user_id, queryset, action_flag, change_message):
    LogEntry.objects.log_actions(
        user_id=user_id,
        queryset=queryset,
        action_flag=action_flag,
        change_message=change_message
    )