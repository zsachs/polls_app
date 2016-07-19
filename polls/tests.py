import datetime

from django.utils import timezone
from django.test import TestCase
from django.core.urlresolvers import reverse

from .models import Question


class QuestionMethodTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() should return False for questions whose
        pub_date is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertEqual(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() should return False for questions whose
        pub_date is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=30)
        old_question = Question(pub_date=time)
        self.assertEqual(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() should return True for questions whose
        pub_date is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=1)
        recent_question = Question(pub_date=time)
        self.assertEqual(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    """
    Creates a question with the given 'question_text' and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)

def create_choices(question):
    """
    Creates two choices for the given question object.
    """
    question.choice_set.create(choice_text='A pinch of Column A.', votes=2)
    question.choice_set.create(choice_text='A dash of Column B.', votes=2)


class QuestionViewTests(TestCase):

    def test_index_view_with_no_questions(self):
        """
        If no questions exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_index_view_with_a_valid_question(self):
        """
        Questions with a pub_date in the past and choices should be displayed
        on the index page.
        """
        question = create_question(question_text="Past question.", days=-30)
        create_choices(question)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_index_view_with_invalid_questions(self):
        """
        Questions with a pub_date in the future or no choices should not be
        displayed on the index page.
        """
        future_question = create_question(question_text="Future question.", days=30)
        create_choices(future_question)
        past_question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_index_view_with_invalid_questions_and_a_valid_question(self):
        """
        Even if past and future questions, with or without choices, exist, only
        past questions with choices should be displayed.
        """
        past_question_1 = create_question(question_text="Past question 1.", days=-30)
        past_question_2 = create_question(question_text="Past question 2.", days=-15)
        create_choices(past_question_2)
        future_question_1 = create_question(question_text="Future question 1.", days=30)
        future_question_2 = create_question(question_text="Future question 2.", days=60)
        create_choices(future_question_2)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>']
        )

    def test_index_view_with_two_valid_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question_1 = create_question(question_text="Past question 1.", days=-30)
        question_2 = create_question(question_text="Past question 2.", days=-5)
        create_choices(question_1)
        create_choices(question_2)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )


class QuestionIndexDetailTests(TestCase):

    def test_detail_view_with_invalid_questions(self):
        """
        The detail view of a question with a pub_date in the future or no
        choices should return a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        create_choices(future_question)
        past_question = create_question(question_text='Past question.', days=-5)
        future_url = reverse('polls:detail', args=(future_question.id,))
        past_url = reverse('polls:detail', args=(past_question.id,))
        future_response = self.client.get(future_url)
        past_response = self.client.get(past_url)
        self.assertEqual(future_response.status_code, 404)
        self.assertEqual(past_response.status_code, 404)

    def test_detail_view_with_a_valid_question(self):
        """
        The detail view of a question with a pub_date in the past and choices
        should display the text of the question and its choices.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        create_choices(past_question)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
        for choice in past_question.choice_set.all():
            self.assertContains(response, choice.choice_text)


class QuestionIndexResultsTests(TestCase):

    def test_results_view_with_invalid_questions(self):
        """
        The results view of a question with a pub_date in the future or no
        choices should return a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        create_choices(future_question)
        past_question = create_question(question_text='Past Question.', days=-5)
        future_url = reverse('polls:results', args=(future_question.id,))
        past_url = reverse('polls:results', args=(past_question.id,))
        future_response = self.client.get(future_url)
        past_response = self.client.get(past_url)
        self.assertEqual(future_response.status_code, 404)
        self.assertEqual(past_response.status_code, 404)

    def test_results_view_with_a_valid_question(self):
        """
        The results view of a question with a pub_date in the past and choices
        should display the question's voting results.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        create_choices(past_question)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
        for choice in past_question.choice_set.all():
            self.assertContains(response, choice.choice_text)
            self.assertContains(response, choice.votes)
