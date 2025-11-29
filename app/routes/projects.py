"""Project routes."""
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Project, Milestone, RewardTier, Category, ProjectUpdate, Comment
from app.utils.validators import (
    validate_project_title, validate_project_description,
    validate_sol_amount, validate_url, sanitize_html
)
from app.utils.decorators import owner_required

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/')
def list_projects():
    """List all active projects with filters."""
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # Filters
    sort = request.args.get('sort', 'newest')  # newest, popular, ending_soon, funded
    status = request.args.get('status', 'active')
    category_slug = request.args.get('category', '')
    search_query = request.args.get('q', '').strip()

    # Get all categories for filter UI
    categories = Category.query.order_by(Category.sort_order).all()

    # Build query - exclude drafts from public listing
    query = Project.query.filter_by(is_draft=False)

    if status == 'active':
        query = query.filter_by(status='active')
    elif status == 'ended':
        query = query.filter_by(status='ended')
    # 'all' shows everything (except drafts)

    # Category filter
    current_category = None
    if category_slug:
        current_category = Category.query.filter_by(slug=category_slug).first()
        if current_category:
            query = query.filter_by(category_id=current_category.id)

    # Search filter
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Project.title.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )

    # Sorting
    if sort == 'newest':
        query = query.order_by(Project.created_at.desc())
    elif sort == 'popular':
        query = query.order_by(Project.raised_sol.desc())
    elif sort == 'ending_soon':
        query = query.filter(Project.end_date > datetime.utcnow())
        query = query.order_by(Project.end_date.asc())
    elif sort == 'funded':
        query = query.order_by(
            (Project.raised_sol / Project.goal_sol).desc()
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'projects/list.html',
        projects=pagination.items,
        pagination=pagination,
        current_sort=sort,
        current_status=status,
        categories=categories,
        current_category=current_category,
        search_query=search_query
    )


@projects_bp.route('/<slug>')
def detail(slug):
    """Project detail page."""
    project = Project.query.filter_by(slug=slug).first_or_404()

    # Draft projects only visible to owner
    if project.is_draft:
        if not current_user.is_authenticated or current_user.id != project.user_id:
            abort(404)

    # Get donations for display
    donations = project.donations.filter_by(status='confirmed').order_by(
        db.desc('created_at')
    ).limit(50).all()

    # Get milestones
    milestones = project.milestones.order_by('sort_order').all()

    # Get reward tiers
    reward_tiers = project.reward_tiers.order_by('sort_order').all()

    # Get top-level comments
    top_comments = project.comments.filter_by(parent_id=None).order_by(
        Comment.created_at.desc()
    ).limit(20).all()

    return render_template(
        'projects/detail.html',
        project=project,
        donations=donations,
        milestones=milestones,
        reward_tiers=reward_tiers,
        top_comments=top_comments
    )


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new project."""
    # Get categories for the form
    categories = Category.query.order_by(Category.sort_order).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        goal_sol = request.form.get('goal_sol', '')
        end_date_str = request.form.get('end_date', '')
        video_url = request.form.get('video_url', '').strip()
        project_website = request.form.get('project_website', '').strip()
        project_twitter = request.form.get('project_twitter', '').strip()
        project_telegram = request.form.get('project_telegram', '').strip()
        project_github = request.form.get('project_github', '').strip()
        project_discord = request.form.get('project_discord', '').strip()
        project_linkedin = request.form.get('project_linkedin', '').strip()
        project_youtube = request.form.get('project_youtube', '').strip()
        category_id = request.form.get('category_id', type=int)

        # Milestones from form
        milestone_titles = request.form.getlist('milestone_title[]')
        milestone_amounts = request.form.getlist('milestone_amount[]')
        milestone_descriptions = request.form.getlist('milestone_description[]')

        # Reward tiers from form
        tier_titles = request.form.getlist('tier_title[]')
        tier_amounts = request.form.getlist('tier_amount[]')
        tier_descriptions = request.form.getlist('tier_description[]')
        tier_limits = request.form.getlist('tier_limit[]')

        errors = []

        # Validation
        if not validate_project_title(title):
            errors.append('Title must be 3-100 characters.')

        if not validate_project_description(description):
            errors.append('Description must be 10-50000 characters.')

        if not validate_sol_amount(goal_sol):
            errors.append('Invalid target amount.')

        try:
            end_date = datetime.fromisoformat(end_date_str)
            if end_date <= datetime.utcnow():
                errors.append('End date must be in the future.')
        except (ValueError, TypeError):
            errors.append('Invalid end date.')

        if video_url and not validate_url(video_url):
            errors.append('Invalid video URL.')

        # Check for unique slug
        slug = Project.generate_slug(title)
        if Project.query.filter_by(slug=slug).first():
            # Add random suffix
            import secrets
            slug = f"{slug}-{secrets.token_hex(3)}"

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('projects/create.html',
                title=title, description=description, goal_sol=goal_sol,
                end_date=end_date_str, video_url=video_url,
                categories=categories, selected_category=category_id
            )

        # Handle image uploads
        uploaded_images = []
        if 'images' in request.files:
            from app.services.storage_service import upload_image as storage_upload
            files = request.files.getlist('images')
            for file in files[:5]:  # Max 5 images
                if file and file.filename:
                    try:
                        image_url = storage_upload(file, folder='projects')
                        uploaded_images.append(image_url)
                    except Exception as e:
                        flash(f'Image upload error: {str(e)}', 'warning')

        # Check if saving as draft
        save_as_draft = request.form.get('save_draft') == '1'

        # Create project
        project = Project(
            user_id=current_user.id,
            category_id=category_id if category_id else None,
            title=title,
            slug=slug,
            description=sanitize_html(description),
            goal_sol=Decimal(str(goal_sol)),
            end_date=end_date,
            video_url=video_url or None,
            project_website=project_website or None,
            project_twitter=project_twitter or None,
            project_telegram=project_telegram or None,
            project_github=project_github or None,
            project_discord=project_discord or None,
            project_linkedin=project_linkedin or None,
            project_youtube=project_youtube or None,
            images=uploaded_images,
            is_draft=save_as_draft
        )

        db.session.add(project)
        db.session.flush()  # Get project ID

        # Add milestones
        for i, (m_title, m_amount, m_desc) in enumerate(
            zip(milestone_titles, milestone_amounts, milestone_descriptions)
        ):
            if m_title.strip() and m_amount:
                try:
                    milestone = Milestone(
                        project_id=project.id,
                        title=m_title.strip(),
                        amount_sol=Decimal(str(m_amount)),
                        description=m_desc.strip() or None,
                        sort_order=i
                    )
                    db.session.add(milestone)
                except (ValueError, TypeError):
                    pass  # Skip invalid milestones

        # Add reward tiers
        for i, (t_title, t_amount, t_desc, t_limit) in enumerate(
            zip(tier_titles, tier_amounts, tier_descriptions, tier_limits)
        ):
            if t_title.strip() and t_amount:
                try:
                    tier = RewardTier(
                        project_id=project.id,
                        title=t_title.strip(),
                        min_amount_sol=Decimal(str(t_amount)),
                        description=t_desc.strip() or None,
                        max_claims=int(t_limit) if t_limit else None,
                        sort_order=i
                    )
                    db.session.add(tier)
                except (ValueError, TypeError):
                    pass  # Skip invalid tiers

        db.session.commit()

        if save_as_draft:
            flash('Project saved as draft. You can publish it later from your dashboard.', 'info')
        else:
            flash('Project created successfully!', 'success')
        return redirect(url_for('projects.detail', slug=project.slug))

    return render_template('projects/create.html', categories=categories)


@projects_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@owner_required(Project)
def edit(id):
    """Edit project."""
    project = Project.query.get_or_404(id)
    categories = Category.query.order_by(Category.sort_order).all()

    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.description = sanitize_html(request.form.get('description', '').strip())
        project.video_url = request.form.get('video_url', '').strip() or None
        project.project_website = request.form.get('project_website', '').strip() or None
        project.project_twitter = request.form.get('project_twitter', '').strip() or None
        project.project_telegram = request.form.get('project_telegram', '').strip() or None
        project.project_github = request.form.get('project_github', '').strip() or None
        project.project_discord = request.form.get('project_discord', '').strip() or None
        project.project_linkedin = request.form.get('project_linkedin', '').strip() or None
        project.project_youtube = request.form.get('project_youtube', '').strip() or None

        # Update category
        category_id = request.form.get('category_id', type=int)
        project.category_id = category_id if category_id else None

        # Can't change goal or end date after donations received
        if project.donation_count == 0:
            goal_sol = request.form.get('goal_sol', '')
            end_date_str = request.form.get('end_date', '')

            if validate_sol_amount(goal_sol):
                project.goal_sol = Decimal(str(goal_sol))

            try:
                end_date = datetime.fromisoformat(end_date_str)
                if end_date > datetime.utcnow():
                    project.end_date = end_date
            except (ValueError, TypeError):
                pass

        db.session.commit()

        flash('Project updated.', 'success')
        return redirect(url_for('projects.detail', slug=project.slug))

    milestones = project.milestones.order_by('sort_order').all()

    return render_template(
        'projects/edit.html',
        project=project,
        milestones=milestones,
        categories=categories
    )


@projects_bp.route('/<int:id>/publish', methods=['POST'])
@login_required
@owner_required(Project)
def publish(id):
    """Publish a draft project."""
    project = Project.query.get_or_404(id)

    if not project.is_draft:
        flash('Project is already published.', 'info')
        return redirect(url_for('projects.detail', slug=project.slug))

    project.is_draft = False
    db.session.commit()

    flash('Project published successfully! It is now visible to everyone.', 'success')
    return redirect(url_for('projects.detail', slug=project.slug))


@projects_bp.route('/<int:id>/unpublish', methods=['POST'])
@login_required
@owner_required(Project)
def unpublish(id):
    """Unpublish a project (convert back to draft)."""
    project = Project.query.get_or_404(id)

    if project.is_draft:
        flash('Project is already a draft.', 'info')
        return redirect(url_for('projects.detail', slug=project.slug))

    if project.donation_count > 0:
        flash('Cannot unpublish project with donations.', 'error')
        return redirect(url_for('projects.detail', slug=project.slug))

    project.is_draft = True
    db.session.commit()

    flash('Project unpublished. It is now a draft.', 'info')
    return redirect(url_for('projects.detail', slug=project.slug))


@projects_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
@owner_required(Project)
def cancel(id):
    """Cancel project (only if no donations)."""
    project = Project.query.get_or_404(id)

    if project.donation_count > 0:
        flash('Cannot cancel project with donations.', 'error')
        return redirect(url_for('projects.detail', slug=project.slug))

    project.status = 'cancelled'
    db.session.commit()

    flash('Project cancelled.', 'info')
    return redirect(url_for('profile.dashboard'))


# ============== Milestones ==============

@projects_bp.route('/<int:id>/milestones', methods=['POST'])
@login_required
@owner_required(Project)
def add_milestone(id):
    """Add milestone to project."""
    project = Project.query.get_or_404(id)

    title = request.form.get('title', '').strip()
    amount_sol = request.form.get('amount_sol', '')
    description = request.form.get('description', '').strip()

    if not title or not validate_sol_amount(amount_sol):
        flash('Invalid milestone data.', 'error')
        return redirect(url_for('projects.edit', id=id))

    # Get next sort order
    max_order = db.session.query(db.func.max(Milestone.sort_order)).filter(
        Milestone.project_id == id
    ).scalar() or 0

    milestone = Milestone(
        project_id=id,
        title=title,
        amount_sol=Decimal(str(amount_sol)),
        description=description or None,
        sort_order=max_order + 1
    )

    db.session.add(milestone)
    db.session.commit()

    flash('Milestone added.', 'success')
    return redirect(url_for('projects.edit', id=id))


@projects_bp.route('/<int:id>/milestones/<int:mid>', methods=['POST', 'DELETE'])
@login_required
@owner_required(Project)
def edit_milestone(id, mid):
    """Edit or delete milestone."""
    project = Project.query.get_or_404(id)
    milestone = Milestone.query.filter_by(id=mid, project_id=id).first_or_404()

    if request.method == 'DELETE' or request.form.get('_method') == 'DELETE':
        db.session.delete(milestone)
        db.session.commit()
        flash('Milestone deleted.', 'info')
        return redirect(url_for('projects.edit', id=id))

    # Update milestone
    milestone.title = request.form.get('title', milestone.title).strip()
    milestone.description = request.form.get('description', '').strip() or None

    amount_sol = request.form.get('amount_sol', '')
    if validate_sol_amount(amount_sol):
        milestone.amount_sol = Decimal(str(amount_sol))

    db.session.commit()

    flash('Milestone updated.', 'success')
    return redirect(url_for('projects.edit', id=id))


# ============== Images ==============

@projects_bp.route('/<int:id>/images', methods=['POST'])
@login_required
@owner_required(Project)
def upload_image(id):
    """Upload image to project."""
    from app.services.storage_service import upload_image as storage_upload

    project = Project.query.get_or_404(id)

    if 'image' not in request.files:
        if request.is_json:
            return jsonify({'error': 'No file'}), 400
        flash('No file.', 'error')
        return redirect(url_for('projects.edit', id=id))

    file = request.files['image']

    if file.filename == '':
        if request.is_json:
            return jsonify({'error': 'No file'}), 400
        flash('No file.', 'error')
        return redirect(url_for('projects.edit', id=id))

    try:
        image_url = storage_upload(file, folder=f'projects/{project.id}')

        if project.images is None:
            project.images = []

        images = list(project.images)
        images.append(image_url)
        project.images = images

        db.session.commit()

        if request.is_json:
            return jsonify({'success': True, 'url': image_url})

        flash('Image uploaded.', 'success')
        return redirect(url_for('projects.edit', id=id))

    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Upload error: {str(e)}', 'error')
        return redirect(url_for('projects.edit', id=id))


@projects_bp.route('/<int:id>/images/<int:index>', methods=['DELETE'])
@login_required
@owner_required(Project)
def delete_image(id, index):
    """Delete image from project."""
    project = Project.query.get_or_404(id)

    if project.images and 0 <= index < len(project.images):
        images = list(project.images)
        images.pop(index)
        project.images = images
        db.session.commit()

        return jsonify({'success': True})

    return jsonify({'error': 'Image not found'}), 404


# ============== API Endpoints ==============

@projects_bp.route('/api/list')
def api_list():
    """API endpoint for project list."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 12, type=int), 50)
    sort = request.args.get('sort', 'newest')
    status = request.args.get('status', 'active')
    category_slug = request.args.get('category', '')
    search_query = request.args.get('q', '').strip()

    query = Project.query

    if status == 'active':
        query = query.filter_by(status='active')
    elif status == 'ended':
        query = query.filter_by(status='ended')

    # Category filter
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)

    # Search filter
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Project.title.ilike(search_term),
                Project.description.ilike(search_term)
            )
        )

    if sort == 'newest':
        query = query.order_by(Project.created_at.desc())
    elif sort == 'popular':
        query = query.order_by(Project.raised_sol.desc())
    elif sort == 'ending_soon':
        query = query.filter(Project.end_date > datetime.utcnow())
        query = query.order_by(Project.end_date.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'projects': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@projects_bp.route('/api/<slug>')
def api_detail(slug):
    """API endpoint for project detail."""
    project = Project.query.filter_by(slug=slug).first_or_404()
    return jsonify(project.to_dict(include_donations=True))


@projects_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """API endpoint for project creation."""
    data = request.get_json()

    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    goal_sol = data.get('goal_sol', '')
    end_date_str = data.get('end_date', '')

    errors = []

    if not validate_project_title(title):
        errors.append('Invalid title.')

    if not validate_project_description(description):
        errors.append('Invalid description.')

    if not validate_sol_amount(goal_sol):
        errors.append('Invalid goal amount.')

    try:
        end_date = datetime.fromisoformat(end_date_str)
        if end_date <= datetime.utcnow():
            errors.append('Date must be in the future.')
    except (ValueError, TypeError):
        errors.append('Invalid date.')

    if errors:
        return jsonify({'errors': errors}), 400

    slug = Project.generate_slug(title)
    if Project.query.filter_by(slug=slug).first():
        import secrets
        slug = f"{slug}-{secrets.token_hex(3)}"

    project = Project(
        user_id=current_user.id,
        title=title,
        slug=slug,
        description=sanitize_html(description),
        goal_sol=Decimal(str(goal_sol)),
        end_date=end_date,
        images=[]
    )

    db.session.add(project)
    db.session.commit()

    return jsonify({
        'success': True,
        'project': project.to_dict()
    }), 201


# ============== Project Updates ==============

@projects_bp.route('/<int:id>/updates')
def list_updates(id):
    """List all updates for a project."""
    project = Project.query.get_or_404(id)
    updates = project.updates.order_by(ProjectUpdate.created_at.desc()).all()

    return render_template(
        'projects/updates.html',
        project=project,
        updates=updates
    )


@projects_bp.route('/<int:id>/updates/new', methods=['GET', 'POST'])
@login_required
@owner_required(Project)
def create_update(id):
    """Create a new update for a project."""
    project = Project.query.get_or_404(id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if len(title) < 3 or len(title) > 200:
            flash('Title must be 3-200 characters.', 'error')
            return render_template('projects/update_form.html', project=project, title=title, content=content)

        if len(content) < 10:
            flash('Content must be at least 10 characters.', 'error')
            return render_template('projects/update_form.html', project=project, title=title, content=content)

        update = ProjectUpdate(
            project_id=project.id,
            user_id=current_user.id,
            title=title,
            content=sanitize_html(content)
        )

        db.session.add(update)
        db.session.commit()

        flash('Update posted successfully!', 'success')
        return redirect(url_for('projects.detail', slug=project.slug))

    return render_template('projects/update_form.html', project=project)


@projects_bp.route('/<int:id>/updates/<int:uid>/edit', methods=['GET', 'POST'])
@login_required
@owner_required(Project)
def edit_update(id, uid):
    """Edit a project update."""
    project = Project.query.get_or_404(id)
    update = ProjectUpdate.query.filter_by(id=uid, project_id=id).first_or_404()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if len(title) < 3 or len(title) > 200:
            flash('Title must be 3-200 characters.', 'error')
            return render_template('projects/update_form.html', project=project, update=update, title=title, content=content)

        if len(content) < 10:
            flash('Content must be at least 10 characters.', 'error')
            return render_template('projects/update_form.html', project=project, update=update, title=title, content=content)

        update.title = title
        update.content = sanitize_html(content)
        db.session.commit()

        flash('Update edited successfully!', 'success')
        return redirect(url_for('projects.detail', slug=project.slug))

    return render_template('projects/update_form.html', project=project, update=update)


@projects_bp.route('/<int:id>/updates/<int:uid>/delete', methods=['POST'])
@login_required
@owner_required(Project)
def delete_update(id, uid):
    """Delete a project update."""
    project = Project.query.get_or_404(id)
    update = ProjectUpdate.query.filter_by(id=uid, project_id=id).first_or_404()

    db.session.delete(update)
    db.session.commit()

    flash('Update deleted.', 'info')
    return redirect(url_for('projects.detail', slug=project.slug))


# ============== Comments ==============

@projects_bp.route('/<int:id>/comments', methods=['POST'])
@login_required
def add_comment(id):
    """Add a comment to a project."""
    project = Project.query.get_or_404(id)

    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)

    if len(content) < 1 or len(content) > 2000:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Comment must be 1-2000 characters.'}), 400
        flash('Comment must be 1-2000 characters.', 'error')
        return redirect(url_for('projects.detail', slug=project.slug))

    # Verify parent comment exists if provided
    if parent_id:
        parent = Comment.query.filter_by(id=parent_id, project_id=id).first()
        if not parent:
            parent_id = None

    comment = Comment(
        project_id=project.id,
        user_id=current_user.id,
        content=content,
        parent_id=parent_id
    )

    db.session.add(comment)
    db.session.commit()

    # Send notifications
    try:
        from app.services.notification_service import notify_new_comment, notify_comment_reply
        if parent_id:
            notify_comment_reply(comment)
        else:
            notify_new_comment(comment)
    except Exception:
        pass  # Don't fail if notification fails

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'comment': comment.to_dict()})

    flash('Comment posted.', 'success')
    return redirect(url_for('projects.detail', slug=project.slug))


@projects_bp.route('/<int:id>/comments/<int:cid>', methods=['DELETE', 'POST'])
@login_required
def delete_comment(id, cid):
    """Delete a comment (owner or project owner only)."""
    project = Project.query.get_or_404(id)
    comment = Comment.query.filter_by(id=cid, project_id=id).first_or_404()

    # Check permission: comment author or project owner
    if current_user.id != comment.user_id and current_user.id != project.user_id and not current_user.is_admin:
        if request.is_json:
            return jsonify({'error': 'Not authorized'}), 403
        flash('Not authorized.', 'error')
        return redirect(url_for('projects.detail', slug=project.slug))

    # Delete replies first
    Comment.query.filter_by(parent_id=cid).delete()
    db.session.delete(comment)
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Comment deleted.', 'info')
    return redirect(url_for('projects.detail', slug=project.slug))


@projects_bp.route('/api/<int:id>/comments')
def api_comments(id):
    """Get comments for a project (API)."""
    project = Project.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    # Get top-level comments only
    pagination = project.comments.filter_by(parent_id=None).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'comments': [c.to_dict(include_replies=True) for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })
