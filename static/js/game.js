/**
 * PixelGuess — Game Logic
 *
 * LocalStorage keys:
 *   pixelguess_stats             → all-time stats object
 *   pixelguess_state_YYYY-MM-DD  → today's game state
 */

const STATS_KEY = 'pixelguess_stats';
const _puzzleDateEl = document.getElementById('puzzle-date');
const todayStr = _puzzleDateEl?.dataset.date;
const STATE_KEY = `pixelguess_state_${todayStr}`;
const isArchive = _puzzleDateEl?.dataset.archive === 'true';
const prevDate = _puzzleDateEl?.dataset.prevDate || '';
const nextDate = _puzzleDateEl?.dataset.nextDate || '';

function formatPuzzleDate(dateStr) {
  if (!dateStr) return '';
  const [year, month, day] = dateStr.split('-').map(Number);
  const monthName = new Date(year, month - 1, 1).toLocaleString('en-US', { month: 'long' });
  const n = day;
  const suffix = (n >= 11 && n <= 13) ? 'th'
    : n % 10 === 1 ? 'st'
    : n % 10 === 2 ? 'nd'
    : n % 10 === 3 ? 'rd' : 'th';
  return `${monthName} ${n}${suffix}`;
}

// ─── Stats helpers ────────────────────────────────────────────────────────────

function defaultStats() {
  return {
    streak: 0,
    maxStreak: 0,
    totalPlayed: 0,
    totalWon: 0,
    guessDistribution: [0, 0, 0, 0, 0, 0],
    lastPlayed: null,
    lastResult: null,
  };
}

function loadStats() {
  try {
    const raw = localStorage.getItem(STATS_KEY);
    return raw ? JSON.parse(raw) : defaultStats();
  } catch {
    return defaultStats();
  }
}

function saveStats(stats) {
  localStorage.setItem(STATS_KEY, JSON.stringify(stats));
}

function updateStats(won, guessCount) {
  const stats = loadStats();
  if (stats.lastPlayed === todayStr) return; // already recorded today
  stats.totalPlayed++;
  if (won) {
    stats.totalWon++;
    stats.streak++;
    stats.maxStreak = Math.max(stats.maxStreak, stats.streak);
    stats.guessDistribution[guessCount - 1]++;
  } else {
    stats.streak = 0;
  }
  stats.lastPlayed = todayStr;
  stats.lastResult = won ? 'win' : 'loss';
  saveStats(stats);
}

// ─── Game state helpers ───────────────────────────────────────────────────────

function defaultState() {
  return {
    date: todayStr,
    guesses: [],
    currentLevel: 1,
    status: 'playing', // 'playing' | 'won' | 'lost'
    answerDisplay: null,
    hint: null,
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STATE_KEY);
    if (!raw) return defaultState();
    const state = JSON.parse(raw);
    // Discard stale state from a previous day
    if (state.date !== todayStr) return defaultState();
    return state;
  } catch {
    return defaultState();
  }
}

function saveState(state) {
  localStorage.setItem(STATE_KEY, JSON.stringify(state));
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

function showImage(imageUrl) {
  const img = document.getElementById('puzzle-image');
  if (img) img.src = imageUrl;
}

function addGuessToHistory(guess, correct) {
  const list = document.getElementById('guess-history');
  const li = document.createElement('li');
  li.textContent = `${correct ? '✅' : '❌'} ${guess}`;
  li.className = correct ? 'correct' : 'wrong';
  list.appendChild(li);
}

function showHint(hintText) {
  const el = document.getElementById('hint');
  if (!el) return;
  el.textContent = `Hint: ${hintText}`;
  el.hidden = false;
}

function showGameOverModal(won, answerDisplay, stats) {
  const state = loadState();
  const guessCount = state.guesses.length;

  document.getElementById('modal-result').textContent = won ? 'You got it! 🎉' : 'Game over!';
  document.getElementById('modal-answer').textContent = answerDisplay || state.answerDisplay || '';
  document.getElementById('modal-guesses').textContent = won
    ? `Guessed in ${guessCount}/6`
    : 'Better luck tomorrow!';

  // Summary stats
  document.getElementById('stat-played').textContent = stats.totalPlayed;
  document.getElementById('stat-won').textContent = stats.totalWon;
  document.getElementById('stat-streak').textContent = stats.streak;
  document.getElementById('stat-max-streak').textContent = stats.maxStreak;

  // Guess distribution bars
  const bars = document.getElementById('distribution-bars');
  bars.innerHTML = '';
  const max = Math.max(...stats.guessDistribution, 1);
  stats.guessDistribution.forEach((count, i) => {
    const pct = Math.round((count / max) * 100);
    const highlight = won && guessCount === i + 1;
    const row = document.createElement('div');
    row.className = 'dist-row';
    row.innerHTML =
      `<span class="dist-label">${i + 1}</span>` +
      `<div class="dist-bar-wrap">` +
        `<div class="dist-bar${highlight ? ' highlight' : ''}" style="width:${Math.max(pct, 4)}%">` +
          `${count || ''}` +
        `</div>` +
      `</div>`;
    bars.appendChild(row);
  });

  // Navigation links under image and in modal
  const linkList = document.getElementById('archive-link-list');
  linkList.innerHTML = '';

  if (prevDate) {
    const tryPrev = document.getElementById('try-previous-link');
    if (tryPrev) {
      tryPrev.href = `/puzzle/${prevDate}/`;
      tryPrev.textContent = `← Try previous puzzle [${formatPuzzleDate(prevDate)}]`;
      document.getElementById('try-previous').hidden = false;
    }
    const a = document.createElement('a');
    a.href = `/puzzle/${prevDate}/`;
    a.textContent = `← Previous puzzle [${formatPuzzleDate(prevDate)}]`;
    a.className = 'archive-link';
    linkList.appendChild(a);
  }

  if (nextDate) {
    const clientToday = new Date().toLocaleDateString('en-CA');
    const nextHref = (nextDate === clientToday) ? '/' : `/puzzle/${nextDate}/`;
    const tryNext = document.getElementById('try-next-link');
    if (tryNext) {
      tryNext.href = nextHref;
      tryNext.textContent = `Go to next puzzle [${formatPuzzleDate(nextDate)}] →`;
      document.getElementById('try-next').hidden = false;
    }
    const a = document.createElement('a');
    a.href = nextHref;
    a.textContent = `Next puzzle [${formatPuzzleDate(nextDate)}] →`;
    a.className = 'archive-link';
    linkList.appendChild(a);
  }

  document.getElementById('archive-links').hidden = (linkList.children.length === 0);

  // Show tab at bottom rather than popping modal straight away
  document.getElementById('stats-tab').hidden = false;
}

function generateShareText(state) {
  const won = state.status === 'won';
  const guessCount = won ? state.guesses.length : 'X';
  const emojis = state.guesses.map((_, i) =>
    won && i === state.guesses.length - 1 ? '✅' : '🟫'
  );
  const text = `PixelGuess ${todayStr}\n${emojis.join('')} (${guessCount}/6)`;

  navigator.clipboard.writeText(text).then(() => {
    const toast = document.getElementById('toast');
    toast.hidden = false;
    setTimeout(() => { toast.hidden = true; }, 2000);
  }).catch(() => {
    // Fallback: select a temp textarea
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    const toast = document.getElementById('toast');
    toast.hidden = false;
    setTimeout(() => { toast.hidden = true; }, 2000);
  });
}

// ─── Core game logic ──────────────────────────────────────────────────────────

function disableInput() {
  document.getElementById('guess-input').disabled = true;
  document.getElementById('submit-btn').disabled = true;
}

async function submitGuess(guess) {
  // Optimistically disable while request is in flight
  document.getElementById('submit-btn').disabled = true;

  const state = loadState();
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content ?? '';

  // Hide any previous suggestion when a new guess is submitted
  const suggestionEl = document.getElementById('guess-suggestion');
  if (suggestionEl) suggestionEl.hidden = true;

  let data;
  try {
    const resp = await fetch('/guess/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
      },
      body: JSON.stringify({
        guess,
        date: todayStr,
        current_level: state.currentLevel,
      }),
    });
    data = await resp.json();
  } catch (err) {
    console.error('Guess request failed:', err);
    document.getElementById('submit-btn').disabled = false;
    return;
  }

  // Fuzzy match — show suggestion, prefill input, don't consume guess
  if (data.did_you_mean) {
    const input = document.getElementById('guess-input');
    input.value = data.did_you_mean;
    showSuggestion(`Did you mean: ${data.did_you_mean}?`);
    document.getElementById('submit-btn').disabled = false;
    return;
  }

  // Record the guess
  state.guesses.push(guess);
  addGuessToHistory(guess, data.correct);
  document.getElementById('attempts-remaining').textContent = 6 - state.guesses.length;

  if (data.correct) {
    state.status = 'won';
    state.answerDisplay = data.answer_display;
    saveState(state);
    if (!isArchive) updateStats(true, state.guesses.length);
    // Show full-resolution image (level 6)
    try {
      const imgResp = await fetch(`/image/${todayStr}/6/`);
      const imgData = await imgResp.json();
      if (imgData.image_url) showImage(imgData.image_url);
    } catch { /* non-fatal */ }
    disableInput();
    showGameOverModal(true, data.answer_display, loadStats());

  } else if (data.game_over) {
    state.status = 'lost';
    state.answerDisplay = data.answer_display;
    saveState(state);
    if (!isArchive) updateStats(false, state.guesses.length);
    // Show full-resolution image (level 6)
    try {
      const imgResp = await fetch(`/image/${todayStr}/6/`);
      const imgData = await imgResp.json();
      if (imgData.image_url) showImage(imgData.image_url);
    } catch { /* non-fatal */ }
    disableInput();
    showGameOverModal(false, data.answer_display, loadStats());

  } else {
    state.currentLevel = data.level;
    if (data.hint) {
      state.hint = data.hint;
      showHint(data.hint);
    }
    if (data.image_url) showImage(data.image_url);
    saveState(state);
    // Ready for next guess
    const input = document.getElementById('guess-input');
    input.value = '';
    input.focus();
    document.getElementById('submit-btn').disabled = false;
  }
}

function showInputError(msg) {
  const el = document.getElementById('guess-error');
  if (!el) return;
  el.textContent = msg;
  el.hidden = false;
}

function clearInputError() {
  const el = document.getElementById('guess-error');
  if (el) el.hidden = true;
}

function showSuggestion(msg) {
  const el = document.getElementById('guess-suggestion');
  if (!el) return;
  el.textContent = msg;
  el.hidden = false;
}

function clearSuggestion() {
  const el = document.getElementById('guess-suggestion');
  if (el) el.hidden = true;
}

function handleSubmit() {
  const input = document.getElementById('guess-input');
  const guess = input.value.trim();
  if (!guess) {
    showInputError('Please enter a guess.');
    return;
  }
  if (guess.length < 2) {
    showInputError('Guess must be at least 2 characters.');
    return;
  }
  clearInputError();
  submitGuess(guess);
}

// ─── Initialisation ───────────────────────────────────────────────────────────

function init() {
  const state = loadState();

  // Show streak badge if player has an active streak
  const stats = loadStats();
  if (stats.streak > 0) {
    const badge = document.getElementById('streak-badge');
    if (badge) {
      document.getElementById('streak-count').textContent = stats.streak;
      badge.hidden = false;
    }
  }

  // Share button always available (including on restored game-over)
  document.getElementById('share-btn').addEventListener('click', () => {
    generateShareText(loadState());
  });

  // Stats tab — tap to reveal modal
  document.getElementById('stats-tab').addEventListener('click', () => {
    document.getElementById('stats-tab').hidden = true;
    document.getElementById('game-over-modal').hidden = false;
  });

  // Modal close button — hide modal, show tab again
  document.getElementById('modal-close').addEventListener('click', () => {
    document.getElementById('game-over-modal').hidden = true;
    document.getElementById('stats-tab').hidden = false;
  });

  // Restore guess history
  state.guesses.forEach((guess, i) => {
    const isWinningGuess = state.status === 'won' && i === state.guesses.length - 1;
    addGuessToHistory(guess, isWinningGuess);
  });

  // Restore attempts counter
  document.getElementById('attempts-remaining').textContent = 6 - state.guesses.length;

  // Restore hint if previously received
  if (state.hint) showHint(state.hint);

  if (state.status !== 'playing') {
    // Already played today — lock input and show modal
    disableInput();
    const levelToShow = (state.status === 'won' || state.status === 'lost') ? 6 : state.currentLevel;
    fetch(`/image/${todayStr}/${levelToShow}/`)
      .then(r => r.json())
      .then(d => { if (d.image_url) showImage(d.image_url); })
      .catch(() => {});
    setTimeout(() => {
      showGameOverModal(state.status === 'won', state.answerDisplay, loadStats());
    }, 150);
    return;
  }

  // Active game — show the correct pixelation level
  if (state.currentLevel > 1) {
    fetch(`/image/${todayStr}/${state.currentLevel}/`)
      .then(r => r.json())
      .then(d => { if (d.image_url) showImage(d.image_url); })
      .catch(() => {});
  }

  // Attach input listeners
  document.getElementById('submit-btn').addEventListener('click', handleSubmit);
  document.getElementById('guess-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleSubmit();
  });
  document.getElementById('guess-input').addEventListener('input', () => {
    clearInputError();
    clearSuggestion();
  });
}

document.addEventListener('DOMContentLoaded', init);
