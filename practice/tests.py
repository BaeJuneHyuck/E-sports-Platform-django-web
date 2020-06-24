import unittest
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.core.handlers.wsgi import WSGIRequest
from django.test import TestCase, Client, RequestFactory

# Create your tests here.
from django.urls import reverse

from practice.forms import PracticeCreateForm, CommentForm
from practice.models import Practice, Comment, PracticeParticipate
from practice.views import DetailView, TotalListView
from user.models import User

client = Client()


class PracticeModelTest(unittest.TestCase):
    @classmethod
    def setUpTestData(cls):
        now = datetime.now()
        practice_time = now + timedelta(days=1)
        user1 = User.objects.create(email='test@test.com', name='user')
        user2 = User.objects.create(email='test2@test.com', name='user2')
        practice = Practice.objects.create(author=user1, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD', practice_time=practice_time)
        user2.save()
        practice.save()

    def test_practice_model(self):
        """
        Test Practice model creating
        """
        practice_time = datetime.now() + timedelta(days=1)
        user = User.objects.create(email='test1@test.com', name='user')
        practice = Practice.objects.create(author=user, title='create practice 1', text='create practice', game='LOL',
                                           tier='GOLD', practice_time=practice_time)
        self.assertTrue(practice)

    def test_comment_model(self):
        """
        Test Comment model creating
        """
        user = User.objects.create(email='test2@test.com', name='user2')
        practice = Practice.objects.create(author=user, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        comment = Comment.objects.create(practice=practice, author=user, content='comment 1')
        self.assertTrue(comment)

    def test_title_max_length(self):
        user = User.objects.create(email='test3@test.com', name='user2')
        practice = Practice.objects.create(author=user, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        max_length = practice._meta.get_field('title').max_length
        self.assertEquals(max_length, 200)

    def test_text_max_length(self):
        user = User.objects.create(email='test4@test.com', name='user2')
        practice = Practice.objects.create(author=user, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        max_length = practice._meta.get_field('text').max_length
        self.assertEquals(max_length, 600)

    def test_total_practice(self):
        """
        total_practice() should return True when total number of practices is equal to
        total_practice
        """
        self.assertEqual(Practice.total_practice(), Practice.objects.count())


class PracticeCreateFormTest(unittest.TestCase):
    def test_renew_form_date(self):
        practice_time = datetime.now() + timedelta(days=1)
        form = PracticeCreateForm(data={'title': 'practice', 'text': 'create practice 1',
                                        'game': 'LOL', 'tier': 'GOLD', 'practice_time': practice_time})
        self.assertTrue(form.is_valid())
        self.assertTrue(form.instance.title, 'practice')
        self.assertTrue(form.instance.text, 'create practice 1')
        self.assertTrue(form.instance.game, 'LOL')
        self.assertTrue(form.instance.tier, 'GOLD')
        self.assertTrue(form.instance.practice_time, practice_time)

    def test_was_practice_time_with_past_time(self):
        """
        was_practice_time_with_past_time() should return False for practice
        whose practice_time is in the past.
        """
        practice_time = datetime.now() - timedelta(days=1)
        form = PracticeCreateForm(data={'title': 'practice past', 'text': 'create practice 1',
                                        'game': 'LOL', 'tier': 'GOLD', 'practice_time': practice_time})
        self.assertFalse(form.is_valid())

    def test_was_practice_time_with_over_three_year(self):
        """
        PracticeCreateForm's is_valid should False when practice_time is over three year.
        """
        practice_time = datetime.now() + relativedelta(years=3) + timedelta(days=1)
        form = PracticeCreateForm(data={'title': 'practice over three year', 'text': 'create practice 1',
                                        'game': 'LOL', 'tier': 'GOLD', 'practice_time': practice_time})
        self.assertFalse(form.is_valid())

    def test_practice_time_is_max(self):
        """
        test_max_practice_time() should
        """
        practice_time = datetime.now() + relativedelta(years=3) - relativedelta(days=1)
        form = PracticeCreateForm(data={'title': 'practice max time', 'text': 'create practice 1',
                                        'game': 'LOL', 'tier': 'GOLD', 'practice_time': practice_time})
        self.assertTrue(form.is_valid())

    def get_crsfToken(self):
        """
        Get csrf token
        """
        response = self.client.get('/practice/list/create/')
        self.assertTrue(response.cookies.get('csrftoken'))


class TotalListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(email='testlist@test.com', name='testlist', password='1q2w3e4r')
        number_of_practice = 13
        for practice_id in range(number_of_practice):
            if practice_id % 2 == 0:
                Practice.objects.create(
                    author=user,
                    title=f'practice {practice_id}',
                    text=f'practice {practice_id}',
                    game='LOL',
                    tier='Master',
                    practice_time=datetime.now() + relativedelta(days=practice_id),
                )
            else:
                Practice.objects.create(
                    author=user,
                    title=f'practice {practice_id}',
                    text=f'practice {practice_id}',
                    game='Overwatch',
                    tier='Master',
                    practice_time=datetime.now() + relativedelta(days=practice_id),
                )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/practice/list')
        self.assertEquals(response.status_code, 301)

    def test_view_url_correct_template(self):
        response = self.client.get(reverse('practice:list'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'practice/list.html')

class IndexViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(email='testindex@test.com', name='testindex', password='1q2w3e4r')
        number_of_practices = 6
        for practice_id in range(number_of_practices):
            Practice.objects.create(
                author=user,
                title=f'practice {practice_id}',
                text=f'practice {practice_id}',
                game='LOL',
                tier='Master',
                practice_time=datetime.now() + relativedelta(days=practice_id),
            )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/practice/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_correct_template(self):
        response = self.client.get(reverse('practice:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'practice/index.html')


class DetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(email='testuser1@test.com', password='1q2w3e4r5t', name='user')
        user.save()
        practice = Practice.objects.create(author=user, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        practice.save()

    def test_redirect_if_not_logged_in(self):
        response = self.client.get('/practice/list/detail/1/')
        self.assertRedirects(response, '/user/login/?next=/practice/list/detail/1/')

    def test_logged_in_uses_correct_template(self):
        user = User.objects.create(email='test1@test.com', name='user2')
        practice = Practice.objects.create(author=user, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        login = self.client.login(email='testuser1@test.com', password='1q2w3e4r5t')
        self.assertTrue(login)
        response = self.client.get(reverse('practice:detail', kwargs={'pk': practice.pk}))

        # Check we userd correct template
        self.assertTemplateUsed(response, 'practice/detail.html')

    def test_create_comment(self):
        user = User.objects.create(email='test1@test.com', name='user2')
        practice = Practice.objects.create(author=user, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        login = self.client.login(email='testuser1@test.com', password='1q2w3e4r5t')
        self.assertTrue(login)
        response = self.client.get(reverse('practice:detail', kwargs={'pk': practice.pk}))
        self.assertTemplateUsed(response, 'practice/detail.html')
        form = CommentForm(data={'content':'참가신청합니다.'})
        self.assertTrue(form.is_valid())
        comment = form.save(commit=False)
        comment.author = response.context["user"]
        comment.practice = practice
        self.assertTrue(form.instance.practice, practice)
        self.assertTrue(form.instance.content, '참가신청합니다.')
        self.assertTrue(form.instance.author.email, 'testuser1@test.com')

    def test_attend(self):
        view = DetailView()
        user = User.objects.create(email='test1@test.com', name='user2')
        practice = Practice.objects.create(author=user, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        login = self.client.login(email='testuser1@test.com', password='1q2w3e4r5t')
        self.assertTrue(login)
        response = self.client.get(reverse('practice:detail', kwargs={'pk': practice.pk}))
        self.assertTemplateUsed(response, 'practice/detail.html')
        form = CommentForm(data={'content':'참가신청합니다.'})
        comment = form.save(commit=False)
        comment.author = response.context["user"]
        comment.practice = practice
        view.object = practice
        view.user = response.context["user"]
        view.particiate(comment)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PracticeParticipate.objects.get(user=response.context["user"], practice=practice))

    def test_delete_comment(self):
        response = self.client.get('/practice/list/detail/1/')
        self.assertRedirects(response, '/user/login/?next=/practice/list/detail/1/')
        view = DetailView()
        practice = Practice.objects.create(author=User.objects.get(email='testuser1@test.com'),
                                           title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        comment = Comment.objects.create(practice=practice, author=User.objects.get(pk=1), content='삭제될 comment')

        login = self.client.login(email='testuser1@test.com', password='1q2w3e4r5t')
        self.assertTrue(login)
        response = self.client.get(reverse('practice:detail', kwargs={'pk': practice.pk}))
        view.user = response.context["user"]
        view.request = response.context['request']
        view.delete(practice.pk, comment.pk)
        remain_comment = Comment.objects.filter(pk=comment.pk)
        self.assertQuerysetEqual(remain_comment, {})

    def test_delete_all_comment(self):
        response = self.client.get('/practice/list/detail/1/')
        self.assertRedirects(response, '/user/login/?next=/practice/list/detail/1/')
        view = DetailView()
        user1 = User.objects.get(email='testuser1@test.com')
        print(user1)
        user2 = User.objects.create(email='test2@test.com', name='user2', password='1q2w3e4r5t')
        practice = Practice.objects.create(author=user1, title='create practice 1',
                                           text='create practice', game='LOL', tier='GOLD',
                                           practice_time=datetime.now() + timedelta(days=1))
        Comment.objects.create(practice=practice, author=user1, content='user1 comment1')
        Comment.objects.create(practice=practice, author=user1, content='user1 comment2')
        Comment.objects.create(practice=practice, author=user1, content='user1 comment3')
        Comment.objects.create(practice=practice, author=user2, content='user2 comment1')
        Comment.objects.create(practice=practice, author=user2, content='user2 comment2')
        Comment.objects.create(practice=practice, author=user1, content='user1 comment4')
        Comment.objects.create(practice=practice, author=user2, content='user2 comment3')

        login = self.client.login(email='testuser1@test.com', password='1q2w3e4r5t')
        self.assertTrue(login)
        response = self.client.get(reverse('practice:detail', kwargs={'pk': practice.pk}))
        view.user = response.context["user"]
        view.request = response.context['request']
        view.delete_all(practice.pk)

        user1Comment = Comment.objects.filter(author=user1)
        self.assertQuerysetEqual(user1Comment, {})
