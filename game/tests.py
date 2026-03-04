import json
from datetime import date
from io import BytesIO
from unittest.mock import patch, MagicMock
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from .models import Puzzle, PuzzleImage


def make_puzzle(answer='eiffel tower', answer_display='Eiffel Tower',
                category='place', puzzle_date=None, hint='A famous landmark'):
    """Create a Puzzle without triggering Pillow image generation."""
    if puzzle_date is None:
        puzzle_date = date.today()
    with patch('game.utils.generate_pixel_levels'):
        puzzle = Puzzle.objects.create(
            date=puzzle_date,
            answer=answer,
            answer_display=answer_display,
            category=category,
            hint=hint,
            image='puzzles/originals/test.jpg',
        )
    return puzzle


# ─── Index view ───────────────────────────────────────────────────────────────

class IndexViewTests(TestCase):
    def test_no_puzzle_returns_200(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No puzzle today')

    def test_puzzle_exists_returns_200(self):
        make_puzzle()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)


# ─── get_image view ───────────────────────────────────────────────────────────

class GetImageViewTests(TestCase):
    def setUp(self):
        self.puzzle = make_puzzle()
        PuzzleImage.objects.create(
            puzzle=self.puzzle, level=1,
            image='puzzles/processed/test_level1.jpg',
        )
        self.date_str = date.today().isoformat()

    def test_returns_image_url(self):
        url = reverse('get_image', args=[self.date_str, 1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('image_url', json.loads(response.content))

    def test_404_on_missing_level(self):
        url = reverse('get_image', args=[self.date_str, 5])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_404_on_bad_date(self):
        url = reverse('get_image', args=['1999-01-01', 1])
        self.assertEqual(self.client.get(url).status_code, 404)


# ─── submit_guess view ────────────────────────────────────────────────────────

class SubmitGuessViewTests(TestCase):
    def setUp(self):
        self.puzzle = make_puzzle(answer='eiffel tower')
        self.date_str = date.today().isoformat()

    def post_guess(self, guess, level=1, date_str=None):
        return self.client.post(
            reverse('submit_guess'),
            data=json.dumps({
                'guess': guess,
                'date': date_str or self.date_str,
                'current_level': level,
            }),
            content_type='application/json',
        )

    # Correct / wrong flow
    def test_correct_guess(self):
        data = json.loads(self.post_guess('eiffel tower').content)
        self.assertTrue(data['correct'])
        self.assertTrue(data['game_over'])
        self.assertEqual(data['answer_display'], 'Eiffel Tower')

    def test_correct_guess_case_insensitive(self):
        data = json.loads(self.post_guess('EIFFEL TOWER').content)
        self.assertTrue(data['correct'])

    def test_correct_guess_strips_whitespace(self):
        data = json.loads(self.post_guess('  eiffel tower  ').content)
        self.assertTrue(data['correct'])

    def test_wrong_guess_not_game_over(self):
        data = json.loads(self.post_guess('big ben', level=1).content)
        self.assertFalse(data['correct'])
        self.assertFalse(data['game_over'])
        self.assertEqual(data['level'], 2)

    def test_wrong_guess_at_level_6_is_game_over(self):
        data = json.loads(self.post_guess('wrong answer', level=6).content)
        self.assertFalse(data['correct'])
        self.assertTrue(data['game_over'])
        self.assertEqual(data['answer_display'], 'Eiffel Tower')

    def test_hint_appears_after_3_wrong_guesses(self):
        data = json.loads(self.post_guess('wrong', level=3).content)
        self.assertIn('hint', data)

    def test_no_hint_before_3_wrong_guesses(self):
        data = json.loads(self.post_guess('wrong', level=1).content)
        self.assertNotIn('hint', data)

    # HTTP method enforcement
    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse('submit_guess')).status_code, 405)

    # Bad input — server side
    def test_invalid_json(self):
        resp = self.client.post(
            reverse('submit_guess'), data='not json',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_bad_date_returns_404(self):
        self.assertEqual(self.post_guess('test', date_str='1999-01-01').status_code, 404)

    def test_empty_guess_returns_400(self):
        resp = self.post_guess('')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', json.loads(resp.content))

    def test_whitespace_only_guess_returns_400(self):
        resp = self.post_guess('   ')
        self.assertEqual(resp.status_code, 400)

    def test_invalid_level_string_returns_400(self):
        resp = self.client.post(
            reverse('submit_guess'),
            data=json.dumps({'guess': 'test', 'date': self.date_str, 'current_level': 'abc'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_level_out_of_range_returns_400(self):
        resp = self.client.post(
            reverse('submit_guess'),
            data=json.dumps({'guess': 'test', 'date': self.date_str, 'current_level': 7}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)


# ─── Fuzzy guess matching ─────────────────────────────────────────────────────

class FuzzyGuessTests(TestCase):
    def setUp(self):
        self.puzzle = make_puzzle(answer='banana', answer_display='Banana', hint='')
        self.date_str = date.today().isoformat()

    def post_guess(self, guess, level=1):
        return self.client.post(
            reverse('submit_guess'),
            data=json.dumps({
                'guess': guess,
                'date': self.date_str,
                'current_level': level,
            }),
            content_type='application/json',
        )

    def test_close_typo_returns_did_you_mean(self):
        data = json.loads(self.post_guess('bannana').content)
        self.assertFalse(data['correct'])
        self.assertFalse(data['game_over'])
        self.assertIn('did_you_mean', data)

    def test_did_you_mean_contains_answer_display(self):
        data = json.loads(self.post_guess('bannana').content)
        self.assertEqual(data['did_you_mean'], 'Banana')

    def test_close_typo_does_not_advance_level(self):
        data = json.loads(self.post_guess('bannana', level=1).content)
        self.assertNotIn('level', data)
        self.assertNotIn('image_url', data)

    def test_exact_match_still_correct(self):
        data = json.loads(self.post_guess('banana').content)
        self.assertTrue(data['correct'])
        self.assertTrue(data['game_over'])

    def test_far_off_guess_is_normal_wrong(self):
        data = json.loads(self.post_guess('paris', level=1).content)
        self.assertFalse(data['correct'])
        self.assertFalse(data['game_over'])
        self.assertNotIn('did_you_mean', data)
        self.assertEqual(data['level'], 2)

    def test_below_threshold_is_wrong_guess(self):
        # 'xyz' vs 'banana' is well below 0.75
        data = json.loads(self.post_guess('xyz', level=1).content)
        self.assertNotIn('did_you_mean', data)
        self.assertEqual(data['level'], 2)


# ─── Management command ───────────────────────────────────────────────────────

class CreatePuzzleCommandTests(TestCase):
    def _make_image_file(self, tmp_path):
        """Write a minimal valid JPEG to a temp path and return it."""
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(str(tmp_path), format='JPEG')

    def test_bad_date_raises(self):
        with self.assertRaises(CommandError):
            call_command('create_puzzle',
                         date='not-a-date', answer='x', answer_display='X',
                         category='place', image='/tmp/x.jpg')

    def test_missing_image_raises(self):
        with self.assertRaises(CommandError):
            call_command('create_puzzle',
                         date='2099-01-01', answer='x', answer_display='X',
                         category='place', image='/nonexistent/path.jpg')

    def test_duplicate_date_raises(self):
        make_puzzle(puzzle_date=date(2099, 1, 1))
        with self.assertRaises(CommandError):
            call_command('create_puzzle',
                         date='2099-01-01', answer='x', answer_display='X',
                         category='place', image='/tmp/x.jpg')

    def test_creates_puzzle_successfully(self):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp = f.name
        self._make_image_file(tmp)
        try:
            with patch('game.utils.generate_pixel_levels'):
                call_command('create_puzzle',
                             date='2099-02-01',
                             answer='big ben',
                             answer_display='Big Ben',
                             category='place',
                             hint='A clock tower',
                             image=tmp)
        finally:
            os.unlink(tmp)

        puzzle = Puzzle.objects.get(date=date(2099, 2, 1))
        self.assertEqual(puzzle.answer, 'big ben')
        self.assertEqual(puzzle.answer_display, 'Big Ben')
        self.assertEqual(puzzle.hint, 'A clock tower')
