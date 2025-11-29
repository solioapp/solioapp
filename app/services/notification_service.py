"""Notification service for creating notifications on various events."""
from flask import url_for

from app.extensions import db
from app.models import Notification


def notify_new_donation(donation):
    """Create notification for project owner when they receive a donation."""
    project = donation.project
    donor_name = donation.donor_display_name

    Notification.create_notification(
        user_id=project.user_id,
        type='donation',
        title=f'New donation: {donation.amount_sol:.4f} SOL',
        message=f'{donor_name} donated to your project "{project.title}"',
        link=url_for('projects.detail', slug=project.slug),
        project_id=project.id,
        donation_id=donation.id
    )
    db.session.commit()


def notify_new_comment(comment):
    """Create notification for project owner when someone comments."""
    project = comment.project
    author = comment.author

    # Don't notify if project owner is commenting on their own project
    if project.user_id == comment.user_id:
        return

    Notification.create_notification(
        user_id=project.user_id,
        type='comment',
        title=f'New comment on "{project.title}"',
        message=f'{author.username}: {comment.content[:100]}{"..." if len(comment.content) > 100 else ""}',
        link=url_for('projects.detail', slug=project.slug),
        project_id=project.id,
        comment_id=comment.id
    )
    db.session.commit()


def notify_comment_reply(reply):
    """Create notification when someone replies to a comment."""
    parent_comment = reply.parent
    if not parent_comment:
        return

    # Don't notify if replying to own comment
    if parent_comment.user_id == reply.user_id:
        return

    project = reply.project
    author = reply.author

    Notification.create_notification(
        user_id=parent_comment.user_id,
        type='reply',
        title=f'{author.username} replied to your comment',
        message=f'{reply.content[:100]}{"..." if len(reply.content) > 100 else ""}',
        link=url_for('projects.detail', slug=project.slug),
        project_id=project.id,
        comment_id=reply.id
    )
    db.session.commit()


def notify_milestone_reached(project, milestone):
    """Create notification when a milestone is reached."""
    Notification.create_notification(
        user_id=project.user_id,
        type='milestone',
        title=f'Milestone reached: {milestone.title}!',
        message=f'Your project "{project.title}" reached the {milestone.amount_sol} SOL milestone!',
        link=url_for('projects.detail', slug=project.slug),
        project_id=project.id
    )
    db.session.commit()


def notify_project_ended(project):
    """Create notification when a project ends."""
    Notification.create_notification(
        user_id=project.user_id,
        type='project_ended',
        title=f'Project ended: {project.title}',
        message=f'Your project raised {project.raised_sol} SOL from {project.donation_count} donors.',
        link=url_for('projects.detail', slug=project.slug),
        project_id=project.id
    )
    db.session.commit()


def notify_payout_completed(project, payout):
    """Create notification when a payout is completed."""
    Notification.create_notification(
        user_id=project.user_id,
        type='payout',
        title=f'Payout completed: {payout.amount_sol} SOL',
        message=f'Funds from "{project.title}" have been sent to your wallet.',
        link=url_for('projects.detail', slug=project.slug),
        project_id=project.id
    )
    db.session.commit()
