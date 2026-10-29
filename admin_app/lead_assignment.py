import logging
from django.db import transaction

logger = logging.getLogger(__name__)

def get_next_round_robin_consultant():
    """
    Selects the next active consultant using persistent round-robin distribution.
    Only active consultants with active User accounts are included in the rotation.
    
    Thread-safe and transaction-safe via atomic lock on SiteSetting.
    Returns:
        User: The Django User instance associated with the selected Consultant, or None if no active consultants exist.
    """
    from admin_app.models import Consultant, SiteSetting

    active_consultants = list(
        Consultant.objects.filter(is_active=True, user__is_active=True)
        .select_related('user')
        .order_by('id')
    )

    if not active_consultants:
        logger.info("No active consultants found for round-robin assignment.")
        return None

    # If only 1 consultant, directly return them
    if len(active_consultants) == 1:
        return active_consultants[0].user

    try:
        with transaction.atomic():
            setting, _ = SiteSetting.objects.select_for_update().get_or_create(
                key='lead_round_robin_last_consultant_id',
                defaults={
                    'value': '0',
                    'description': 'Last consultant ID assigned via round-robin distribution'
                }
            )

            try:
                last_consultant_id = int(setting.value or 0)
            except (ValueError, TypeError):
                last_consultant_id = 0

            # Find position of last_consultant_id in current active list
            found_idx = -1
            for idx, c in enumerate(active_consultants):
                if c.id == last_consultant_id:
                    found_idx = idx
                    break

            # Advance to next consultant in rotation
            next_idx = (found_idx + 1) % len(active_consultants)
            next_consultant = active_consultants[next_idx]

            # Update pointer for next round
            setting.value = str(next_consultant.id)
            setting.save(update_fields=['value', 'updated_at'])

            logger.info(
                "Round-robin assigned lead to consultant %s (ID: %s, User ID: %s)",
                next_consultant.user.get_full_name,
                next_consultant.id,
                next_consultant.user.id
            )
            return next_consultant.user

    except Exception as exc:
        logger.warning(
            "Round-robin transaction lock encountered an exception (%s), using fallback rotation.",
            exc
        )
        # Fallback to first active consultant
        return active_consultants[0].user
