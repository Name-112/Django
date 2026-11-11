from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView
from django.utils import timezone

from .models import Choice, Question, Comment

from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets

from tutorial.quickstart.serializers import GroupSerializer, UserSerializer



class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.request.session["last_poll"] = self.object.id
        return context


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        return (
            Question.objects.filter(pub_date__lte=timezone.now())
            .order_by("-pub_date")[:6]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cookie-based welcome message
        visited = self.request.COOKIES.get("visited_polls")
        if visited:
            context["message"] = "Welcome back to the Polls application."
        else:
            context["message"] = "Welcome to the Polls application."

        # Session-based visit counter
        count = self.request.session.get("visit_count", 0)
        count += 1
        self.request.session["visit_count"] = count
        context["visit_count"] = count

        # Last poll visited
        last_poll_id = self.request.session.get("last_poll")
        last_poll = None
        if last_poll_id:
            try:
                last_poll = Question.objects.get(pk=last_poll_id)
            except Question.DoesNotExist:
                pass

        context["last_poll"] = last_poll
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response.set_cookie("visited_polls", "yes", max_age=120)
        return response

class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ["text"]

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.question = get_object_or_404(
            Question, pk=self.kwargs["question_id"]
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("polls:detail", kwargs={"pk": self.kwargs["question_id"]})

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
