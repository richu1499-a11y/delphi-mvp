from django.contrib import messages
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User

from .models import MagicLink, Panelist, Response, Round, RoundItem, RoundSubmission


def _require_panelist(request):
    panelist_id = request.session.get("panelist_id")
    if not panelist_id:
        return None
    return Panelist.objects.filter(id=panelist_id, is_active=True).first()


def home(request):
    # Handle token login form submission
    if request.method == "POST":
        token = request.POST.get("token", "").strip()
        if token:
            # Clean up the token - extract UUID if they pasted the full URL
            if "/login/" in token:
                import re
                match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', token, re.I)
                if match:
                    token = match.group(0)
            
            try:
                from uuid import UUID
                token_uuid = UUID(token)
                panelist = Panelist.objects.filter(token=token_uuid, is_active=True).first()
                if panelist:
                    request.session["panelist_id"] = panelist.id
                    messages.success(request, f"Welcome, {panelist.name or panelist.email}!")
                    return HttpResponseRedirect(reverse("dashboard"))
                else:
                    messages.error(request, "Invalid token. Please check and try again.")
            except (ValueError, AttributeError):
                messages.error(request, "Invalid token format. Please enter a valid access token.")
        else:
            messages.error(request, "Please enter your access token.")
    
    return render(request, "delphi/home.html")


def dashboard(request):
    panelist = _require_panelist(request)
    if not panelist:
        return HttpResponseRedirect(reverse("home"))

    study = panelist.study
    open_rounds = study.rounds.filter(is_open=True).order_by("number")

    rounds = []
    for r in open_rounds:
        rounds.append(
            {
                "round": r,
                "is_submitted": RoundSubmission.objects.filter(panelist=panelist, round=r).exists(),
            }
        )

    return render(
        request,
        "delphi/dashboard.html",
        {"panelist": panelist, "study": study, "rounds": rounds},
    )


def round_overview(request, round_id):
    panelist = _require_panelist(request)
    if not panelist:
        return HttpResponseRedirect(reverse("home"))

    round_obj = get_object_or_404(Round, id=round_id, study=panelist.study)
    ris = list(round_obj.round_items.select_related("item").order_by('order'))

    submitted = RoundSubmission.objects.filter(panelist=panelist, round=round_obj).first()

    resp_map = {
        r.round_item_id: r
        for r in Response.objects.filter(panelist=panelist, round_item__round=round_obj)
    }

    rows = [{"ri": ri, "response": resp_map.get(ri.id)} for ri in ris]

    total = len(ris)
    answered = sum(1 for row in rows if row["response"] is not None)
    can_submit = (submitted is None) and (total > 0) and (answered == total)

    return render(
        request,
        "delphi/round_overview.html",
        {
            "panelist": panelist,
            "round": round_obj,
            "rows": rows,
            "submitted": submitted,
            "total": total,
            "answered": answered,
            "can_submit": can_submit,
        },
    )


@require_POST
def submit_round(request, round_id):
    panelist = _require_panelist(request)
    if not panelist:
        return HttpResponseRedirect(reverse("home"))

    round_obj = get_object_or_404(Round, id=round_id, study=panelist.study)

    existing = RoundSubmission.objects.filter(panelist=panelist, round=round_obj).first()
    if existing:
        messages.info(request, "This round is already submitted and locked.")
        return HttpResponseRedirect(reverse("round_overview", kwargs={"round_id": round_obj.id}))

    total = round_obj.round_items.count()
    answered = Response.objects.filter(panelist=panelist, round_item__round=round_obj).count()

    if total == 0:
        messages.error(request, "This round has no items yet.")
        return HttpResponseRedirect(reverse("round_overview", kwargs={"round_id": round_obj.id}))

    if answered < total:
        messages.error(
            request,
            f"Please answer all items before submitting (answered {answered}/{total}).",
        )
        return HttpResponseRedirect(reverse("round_overview", kwargs={"round_id": round_obj.id}))

    RoundSubmission.objects.create(panelist=panelist, round=round_obj)
    messages.success(request, "Submitted. Your responses are now locked.")
    return HttpResponseRedirect(reverse("round_overview", kwargs={"round_id": round_obj.id}))


def item_detail(request, round_item_id):
    panelist = _require_panelist(request)
    if not panelist:
        return HttpResponseRedirect(reverse("home"))

    ri = get_object_or_404(RoundItem, id=round_item_id, round__study=panelist.study)
    round_obj = ri.round

    submitted = RoundSubmission.objects.filter(panelist=panelist, round=round_obj).first()
    locked = submitted is not None

    resp = Response.objects.filter(panelist=panelist, round_item=ri).first()

    # Get all items for navigation - IMPORTANT: order by 'order' field
    all_items = list(round_obj.round_items.order_by('order'))
    current_index = -1
    for i, item in enumerate(all_items):
        if item.id == ri.id:
            current_index = i
            break

    if request.method == "POST":
        if locked:
            messages.error(request, "This round has been submitted. Responses are locked.")
            return HttpResponseRedirect(reverse("round_overview", kwargs={"round_id": round_obj.id}))

        value = None

        # Get the value based on question type
        if ri.item.item_type == 'likert5':
            value = request.POST.get("value", "").strip()

        elif ri.item.item_type == 'yesno':
            value = request.POST.get("value", "").strip()

        elif ri.item.item_type == 'multiple':
            value = request.POST.get("value", "").strip()
            other_text = request.POST.get("other_text", "").strip()
            if value and other_text:
                option_text = ""
                if value == "A" and ri.item.option_a:
                    option_text = ri.item.option_a.lower()
                elif value == "B" and ri.item.option_b:
                    option_text = ri.item.option_b.lower()
                elif value == "C" and ri.item.option_c:
                    option_text = ri.item.option_c.lower()
                elif value == "D" and ri.item.option_d:
                    option_text = ri.item.option_d.lower()
                elif value == "E" and ri.item.option_e:
                    option_text = ri.item.option_e.lower()
                elif value == "F" and ri.item.option_f:
                    option_text = ri.item.option_f.lower()
                
                if "other" in option_text:
                    value = f"Other: {other_text}"

        elif ri.item.item_type == 'checkbox':
            values = request.POST.getlist("checkbox_value")
            other_text = request.POST.get("cb_other_text", "").strip()
            
            if values:
                final_values = []
                for v in values:
                    option_text = ""
                    if v == "A" and ri.item.option_a:
                        option_text = ri.item.option_a.lower()
                    elif v == "B" and ri.item.option_b:
                        option_text = ri.item.option_b.lower()
                    elif v == "C" and ri.item.option_c:
                        option_text = ri.item.option_c.lower()
                    elif v == "D" and ri.item.option_d:
                        option_text = ri.item.option_d.lower()
                    elif v == "E" and ri.item.option_e:
                        option_text = ri.item.option_e.lower()
                    elif v == "F" and ri.item.option_f:
                        option_text = ri.item.option_f.lower()
                    
                    if "other" in option_text and other_text:
                        final_values.append(f"Other: {other_text}")
                    else:
                        final_values.append(v)
                value = ",".join(final_values)
            else:
                value = ""

        elif ri.item.item_type == 'matrix':
            value = request.POST.get("value", "").strip()
            if value == "" or value == "{}":
                value = ""

        elif ri.item.item_type == 'text':
            value = request.POST.get("value", "").strip()

        else:
            value = request.POST.get("value", "").strip()

        # Check if we have a valid response
        if value:
            # Save the response
            Response.objects.update_or_create(
                panelist=panelist, round_item=ri, defaults={"value": value}
            )
            messages.success(request, "Saved.")
            
            # Navigate to next item or back to overview
            if current_index >= 0 and current_index < len(all_items) - 1:
                next_item = all_items[current_index + 1]
                return HttpResponseRedirect(reverse("item_detail", kwargs={"round_item_id": next_item.id}))
            else:
                return HttpResponseRedirect(reverse("round_overview", kwargs={"round_id": round_obj.id}))
        else:
            messages.error(request, "Please provide a response before continuing.")

    # GET request or failed validation - render the page
    feedback_allowed = True
    if round_obj.number == 1 and not round_obj.show_feedback_immediately:
        has_any = Response.objects.filter(panelist=panelist, round_item__round=round_obj).exists()
        feedback_allowed = has_any

    agg = None
    if feedback_allowed and ri.item.item_type == "likert5":
        agg = Response.objects.filter(round_item=ri).aggregate(mean=Avg("value"))

    total_items = len(all_items)
    progress_percent = int(((current_index + 1) / total_items) * 100) if total_items > 0 else 0

    prev_item = all_items[current_index - 1] if current_index > 0 else None
    next_item = all_items[current_index + 1] if current_index < len(all_items) - 1 else None

    current_value = resp.value if resp else ""
    
    selected_option = ""
    other_text = ""
    if ri.item.item_type == 'multiple' and current_value:
        if current_value.startswith("Other:"):
            other_text = current_value.replace("Other:", "").strip()
            if ri.item.option_a and "other" in ri.item.option_a.lower():
                selected_option = "A"
            elif ri.item.option_b and "other" in ri.item.option_b.lower():
                selected_option = "B"
            elif ri.item.option_c and "other" in ri.item.option_c.lower():
                selected_option = "C"
            elif ri.item.option_d and "other" in ri.item.option_d.lower():
                selected_option = "D"
            elif ri.item.option_e and "other" in ri.item.option_e.lower():
                selected_option = "E"
            elif ri.item.option_f and "other" in ri.item.option_f.lower():
                selected_option = "F"
        else:
            selected_option = current_value
    
    cb_other_text = ""
    if ri.item.item_type == 'checkbox' and current_value:
        parts = current_value.split(",")
        for part in parts:
            if part.startswith("Other:"):
                cb_other_text = part.replace("Other:", "").strip()
                break

    matrix_rows = []
    matrix_columns = []
    current_matrix_value = {}
    
    if ri.item.item_type == 'matrix':
        matrix_rows = ri.item.get_matrix_rows()
        matrix_columns = ri.item.get_matrix_columns()
        if current_value:
            import json
            try:
                current_matrix_value = json.loads(current_value)
            except json.JSONDecodeError:
                current_matrix_value = {}

    return render(
        request,
        "delphi/item_detail.html",
        {
            "panelist": panelist,
            "round_item": ri,
            "response": resp,
            "aggregate": agg,
            "feedback_allowed": feedback_allowed,
            "locked": locked,
            "submitted": submitted,
            "total_items": total_items,
            "progress_percent": progress_percent,
            "prev_item": prev_item,
            "next_item": next_item,
            "current_value": current_value,
            "selected_option": selected_option,
            "other_text": other_text,
            "cb_other_text": cb_other_text,
            "matrix_rows": matrix_rows,
            "matrix_columns": matrix_columns,
            "current_matrix_value": current_matrix_value,
        },
    )


def token_login(request, token):
    """Login using the panelist's permanent token."""
    panelist = get_object_or_404(Panelist, token=token)
    
    if not panelist.is_active:
        messages.error(request, "Your account has been deactivated. Please contact the study administrator.")
        return HttpResponseRedirect(reverse("home"))
    
    request.session["panelist_id"] = panelist.id
    
    messages.success(request, f"Welcome, {panelist.name or panelist.email}!")
    return HttpResponseRedirect(reverse("dashboard"))


def magic_login(request, token):
    magic = get_object_or_404(MagicLink, token=token)
    if not magic.is_valid():
        messages.error(request, "That link is invalid or expired.")
        return HttpResponseRedirect(reverse("home"))

    request.session["panelist_id"] = magic.panelist_id

    next_url = request.GET.get("next", "")
    if next_url.startswith("/"):
        return HttpResponseRedirect(next_url)

    return HttpResponseRedirect(reverse("dashboard"))


def logout_view(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return HttpResponseRedirect(reverse("home"))


def setup_admin(request):
    """One-time setup view to create admin user"""
    secret_key = request.GET.get('key')
    
    if secret_key != 'delphi2024secret':
        return HttpResponse('Not authorized', status=403)
    
    existing = User.objects.filter(username='admin').first()
    if existing:
        existing.delete()
    
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    
    user.refresh_from_db()
    
    return HttpResponse(
        f'Admin user created!<br><br>'
        f'Username: admin<br>'
        f'Password: admin123<br><br>'
        f'is_staff: {user.is_staff}<br>'
        f'is_superuser: {user.is_superuser}<br>'
        f'is_active: {user.is_active}<br><br>'
        f'<strong>CHANGE YOUR PASSWORD after login, then DELETE this endpoint!</strong>'
    )


def run_migrations(request):
    """One-time migration view"""
    secret_key = request.GET.get('key')
    
    if secret_key != 'delphi2024secret':
        return HttpResponse('Not authorized', status=403)
    
    from django.core.management import call_command
    
    output_messages = []
    
    try:
        call_command('migrate', '--noinput')
        output_messages.append("Migrations completed successfully!")
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            output_messages.append("Admin user created (admin / admin123)")
        else:
            output_messages.append("Admin user already exists - no changes needed")
        
        result = "<br>".join(output_messages)
        return HttpResponse(
            f'{result}<br><br>'
            f'<strong>All done! Go to /admin/ to continue.</strong>'
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(
            f'<h3>Error:</h3>'
            f'<p>{str(e)}</p>'
            f'<h3>Details:</h3>'
            f'<pre>{error_details}</pre>',
            status=500
        )


def load_questions_view(request):
    """One-time view to load questions into production database"""
    secret_key = request.GET.get('key')
    
    if secret_key != 'delphi2024secret':
        return HttpResponse('Not authorized', status=403)
    
    from django.core.management import call_command
    from io import StringIO
    
    try:
        out = StringIO()
        call_command('load_questions', stdout=out)
        output = out.getvalue()
        
        return HttpResponse(
            f'<h3>Questions Loaded Successfully!</h3>'
            f'<pre>{output}</pre>'
            f'<br><br>'
            f'<strong>Go to /admin/ to verify the questions.</strong>'
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return HttpResponse(
            f'<h3>Error:</h3>'
            f'<p>{str(e)}</p>'
            f'<h3>Details:</h3>'
            f'<pre>{error_details}</pre>',
            status=500
        )