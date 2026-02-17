from django.contrib import messages
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST


from .models import MagicLink, Panelist, Response, Round, RoundItem, RoundSubmission


def _require_panelist(request):
    panelist_id = request.session.get("panelist_id")
    if not panelist_id:
        return None
    return Panelist.objects.filter(id=panelist_id, is_active=True).first()


def home(request):
    return render(request, "delphi/home.html")


def dashboard(request):
    panelist = _require_panelist(request)
    if not panelist:
        return redirect("home")

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
        return redirect("home")

    round_obj = get_object_or_404(Round, id=round_id, study=panelist.study)
    ris = list(round_obj.round_items.select_related("item").all())

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
        return redirect("home")

    round_obj = get_object_or_404(Round, id=round_id, study=panelist.study)

    existing = RoundSubmission.objects.filter(panelist=panelist, round=round_obj).first()
    if existing:
        messages.info(request, "This round is already submitted and locked.")
        return redirect("round_overview", round_id=round_obj.id)

    total = round_obj.round_items.count()
    answered = Response.objects.filter(panelist=panelist, round_item__round=round_obj).count()

    if total == 0:
        messages.error(request, "This round has no items yet.")
        return redirect("round_overview", round_id=round_obj.id)

    if answered < total:
        messages.error(
            request,
            f"Please answer all items before submitting (answered {answered}/{total}).",
        )
        return redirect("round_overview", round_id=round_obj.id)

    RoundSubmission.objects.create(panelist=panelist, round=round_obj)
    messages.success(request, "Submitted. Your responses are now locked.")
    return redirect("round_overview", round_id=round_obj.id)


def item_detail(request, round_item_id):
    panelist = _require_panelist(request)
    if not panelist:
        return redirect("home")

    ri = get_object_or_404(RoundItem, id=round_item_id, round__study=panelist.study)
    round_obj = ri.round

    submitted = RoundSubmission.objects.filter(panelist=panelist, round=round_obj).first()
    locked = submitted is not None

    resp = Response.objects.filter(panelist=panelist, round_item=ri).first()

    if request.method == "POST":
        if locked:
            messages.error(request, "This round has been submitted. Responses are locked.")
            return redirect("round_overview", round_id=round_obj.id)

        value = request.POST.get("value", "").strip()
        if not value:
            messages.error(request, "Please provide a response.")
        else:
            Response.objects.update_or_create(
                panelist=panelist, round_item=ri, defaults={"value": value}
            )
            messages.success(request, "Saved.")

        return redirect("round_overview", round_id=round_obj.id)

    feedback_allowed = True
    if round_obj.number == 1 and not round_obj.show_feedback_immediately:
        has_any = Response.objects.filter(panelist=panelist, round_item__round=round_obj).exists()
        feedback_allowed = has_any

    agg = None
    if feedback_allowed and ri.item.item_type == "likert5":
        agg = Response.objects.filter(round_item=ri).aggregate(mean=Avg("value"))

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
        },
    )


def magic_login(request, token):
    magic = get_object_or_404(MagicLink, token=token)
    if not magic.is_valid():
        messages.error(request, "That link is invalid or expired.")
        return redirect("home")

    # Reusable link: we don't mark it as used here.
    request.session["panelist_id"] = magic.panelist_id

    # Optional deep-link: /magic/<token>/?next=/round/1/
    next_url = request.GET.get("next", "")
    if next_url.startswith("/"):
        return redirect(next_url)

    return redirect("dashboard")


def logout_view(request):
    request.session.flush()
    messages.success(request, "Logged out.")
    return redirect("home")


