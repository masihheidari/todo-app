from django import forms

from .models import Task


class TaskForm(forms.ModelForm):

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.save()
        return super().form_valid(form)

    class Meta:
        model = Task
        fields = ["title", "is_done", "content"]
