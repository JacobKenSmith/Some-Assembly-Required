const phrase = document.querySelector('#phrase');
const note = document.querySelector('#reception');
const passage = document.querySelector('.passage');

if (new URLSearchParams(location.search).get('view') === 'mobile') {
  document.body.classList.add('mobile-preview');
}

function alignNote() {
  const phraseBounds = phrase.getBoundingClientRect();
  const passageBounds = passage.getBoundingClientRect();
  note.style.setProperty('--anchor', `${Math.max(0, phraseBounds.top - passageBounds.top - 12)}px`);
}

function setNoteOpen(open) {
  note.hidden = !open;
  phrase.setAttribute('aria-expanded', String(open));
  if (open) alignNote();
}

phrase.addEventListener('click', event => {
  event.preventDefault();
  setNoteOpen(note.hidden);
});
phrase.addEventListener('keydown', event => {
  if (event.key === ' ') {
    event.preventDefault();
    setNoteOpen(note.hidden);
  }
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !note.hidden) {
    setNoteOpen(false);
    phrase.focus({ preventScroll: true });
  }
});

const observer = new ResizeObserver(alignNote);
observer.observe(passage);
alignNote();
