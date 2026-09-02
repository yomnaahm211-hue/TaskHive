from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from openai import OpenAI

from .forms import RegisterForm, TaskForm, BidForm
from .models import Task, Bid


def home(request):
    tasks = (
        Task.objects
        .filter(status="Open")
        .select_related("created_by")
        .order_by("-created_at")
    )

    return render(
        request,
        "tasks/home.html",
        {"tasks": tasks},
    )


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "tasks/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Welcome back!")
            return redirect("home")
    else:
        form = AuthenticationForm()

    return render(request, "tasks/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.status = "Open"
            task.save()

            messages.success(request, "Your task has been posted!")
            return redirect("task_detail", task_id=task.id)
    else:
        form = TaskForm()

    return render(request, "tasks/create_task.html", {"form": form})


def task_detail(request, task_id):
    task = get_object_or_404(
        Task.objects.select_related("created_by"),
        id=task_id
    )

    bids = task.bids.select_related("freelancer").order_by("-created_at")

    try:
        risk_analysis = analyze_task_risks(task)
    except Exception as e:
        risk_analysis = f"AI error: {e}"

    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
            "bids": bids,
            "risk_analysis": risk_analysis,
        },
    )


@login_required
def create_bid(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.created_by == request.user:
        messages.error(request, "You cannot bid on your own task.")
        return redirect("task_detail", task_id=task.id)

    if task.status != "Open":
        messages.error(request, "This task is no longer open for bids.")
        return redirect("task_detail", task_id=task.id)

    if request.method == "POST":
        form = BidForm(request.POST)

        if form.is_valid():
            bid = form.save(commit=False)
            bid.task = task
            bid.freelancer = request.user
            bid.save()

            messages.success(request, "Your bid has been submitted!")
            return redirect("task_detail", task_id=task.id)
    else:
        form = BidForm()

    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
            "bids": task.bids.select_related("freelancer"),
            "form": form,
            "show_bid_form": True,
        },
    )


@login_required
def choose_bid(request, task_id, bid_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        created_by=request.user
    )

    bid = get_object_or_404(
        Bid,
        id=bid_id,
        task=task
    )

    task.status = "Assigned"
    task.save()

    messages.success(
        request,
        f"Bid by {bid.freelancer.username} has been selected!"
    )

    return redirect("task_detail", task_id=task.id)


def analyze_task_risks(task):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""
Analyze this freelance task and identify exactly two possible project risks.

Title: {task.title}
Description: {task.description}
Category: {task.category}
Budget: {task.budget}

For each risk, give:
1. Risk name
2. Short explanation
3. One simple recommendation

Keep the answer concise.
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt
    )

    return response.output_text