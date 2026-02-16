from __future__ import annotations

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import Likert5Form, EitherOrForm
from .models import MagicLink, Panelist, Round, RoundItem, Response, Item
from .services import compute_feedback_for_round_item


SESSION_PANELIST_ID = "edelphi_panelist_id"


def _require_panelist(request: HttpRequest) -> Panelist:
    pid = request.session.get(SESSION_PANELIST_ID)
    if not pid:
        raise PermissionError("Not authenticated")
    panelist = get_object_or_404(Panelist, id=pid, is_active=True)
    return panelist


def home(request: HttpRequest) -> HttpResponse:
    # If logged in, go to dashboard.
    if request.session.get(SESSION_PANELIST_ID):
        return redirect("delphi:dashboard")
    return render(request, "delphi/home.html")


def magic_login(request: HttpRequest, token: str) -> HttpResponse:
    link = get_object_or_404(MagicLink, token=token)
    if not link.is_valid:
        return render(request, "delphi/login_invalid.html", {"link": link})
    link.used_at = timezone.now()
    link.save(update_fields=["used_at"])
    request.session[SESSION_PANELIST_ID] = link.panelist_id
    return redirect("delphi:dashboard")


def logout(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    return redirect("delphi:home")


def dashboard(request: HttpRequest) -> HttpResponse:
    try:
        panelist = _require_panelist(request)
    except PermissionError:
        return redirect("delphi:home")

    rounds = Round.objects.filter(study=panelist.study).order_by("number")
    open_round = next((r for r in rounds if r.is_open), None)

    return render(
        request,
        "delphi/dashboard.html",
        {"panelist": panelist, "rounds": rounds, "open_round": open_round},
    )


def round_overview(request: HttpRequest, round_id: int) -> HttpResponse:
    panelist = _require_panelist(request)
    rnd = get_object_or_404(Round, id=round_id, study=panelist.study)

    round_items = RoundItem.objects.filter(round=rnd).select_related("item").order_by("item__order_index", "item__stable_code")

    # Completion: response exists for each item
    responded_ids = set(
        Response.objects.filter(round_item__round=rnd, panelist=panelist).values_list("round_item_id", flat=True)
    )
    items_ctx = []
    for ri in round_items:
        items_ctx.append(
            {"round_item": ri, "item": ri.item, "is_done": ri.id in responded_ids}
        )

    done_count = sum(1 for x in items_ctx if x["is_done"])
    total = len(items_ctx)

    return render(
        request,
        "delphi/round_overview.html",
        {"panelist": panelist, "round": rnd, "items": items_ctx, "done_count": done_count, "total": total},
    )


def item_detail(request: HttpRequest, round_item_id: int) -> HttpResponse:
    panelist = _require_panelist(request)
    ri = get_object_or_404(RoundItem.objects.select_related("round", "item", "round__study"), id=round_item_id)
    rnd = ri.round
    if ri.round.study_id != panelist.study_id:
        return HttpResponseForbidden("Wrong study")

    # Load existing response if any
    resp = Response.objects.filter(round_item=ri, panelist=panelist).first()

    if ri.item.response_type == Item.ResponseType.LIKERT_5:
        form = Likert5Form(request.POST or None, initial={
            "likert_value": str(resp.likert_value) if resp and resp.likert_value else None,
            "comment": resp.comment if resp else "",
            "suggested_revision": resp.suggested_revision if resp else "",
        })
    else:
        form = EitherOrForm(request.POST or None, initial={
            "either_or_value": resp.either_or_value if resp else None,
            "comment": resp.comment if resp else "",
            "suggested_revision": resp.suggested_revision if resp else "",
        })
        form.set_option_labels(ri.item.option_a or "Option A", ri.item.option_b or "Option B")

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        resp, _ = Response.objects.get_or_create(round_item=ri, panelist=panelist)
        resp.comment = data.get("comment", "")
        resp.suggested_revision = data.get("suggested_revision", "")

        if ri.item.response_type == Item.ResponseType.LIKERT_5:
            resp.likert_value = int(data["likert_value"])
            resp.either_or_value = None
        else:
            resp.either_or_value = data["either_or_value"]
            resp.likert_value = None

        resp.save()
        # Update feedback cache (real-time behavior)
        compute_feedback_for_round_item(ri, overwrite=True)
        return redirect("delphi:item_detail", round_item_id=ri.id)

    # Feedback gating logic:
    # Protocol: show group average only after first submission for round 1; in later rounds can show immediately.
    feedback_allowed = False
    if rnd.show_feedback_immediately:
        feedback_allowed = True
    else:
        # allowed after participant has submitted at least one response in this round
        has_any = Response.objects.filter(round_item__round=rnd, panelist=panelist).exists()
        feedback_allowed = has_any

    feedback = None
    if feedback_allowed:
        feedback = getattr(ri, "feedback", None)
        if feedback is None:
            feedback = compute_feedback_for_round_item(ri, overwrite=True)

    # Prior round rating (optional) – used in 2-round workflows
    prior = None
    if rnd.show_prior_round_rating and rnd.number > 1:
        prior_round = Round.objects.filter(study=rnd.study, number=rnd.number - 1).first()
        if prior_round:
            prior_ri = RoundItem.objects.filter(round=prior_round, item__stable_code=ri.item.stable_code, item__version=ri.item.version).first()
            if prior_ri:
                prior = Response.objects.filter(round_item=prior_ri, panelist=panelist).first()

    return render(
        request,
        "delphi/item_detail.html",
        {
            "panelist": panelist,
            "round": rnd,
            "round_item": ri,
            "item": ri.item,
            "form": form,
            "response": resp,
            "feedback_allowed": feedback_allowed,
            "feedback": feedback,
            "prior": prior,
        },
    )
