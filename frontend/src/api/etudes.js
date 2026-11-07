// Calls to the Django backend's etude endpoints (backend/trainer/urls.py).

// The difficulty slider uses 1-3; the API takes names.
const DIFFICULTY_NAMES = { 1: 'easy', 2: 'medium', 3: 'hard' };

export async function generateEtude({ difficulty }) {
    const response = await fetch('/api/generate-etude/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ difficulty: DIFFICULTY_NAMES[Number(difficulty)] }),
    });
    return response.json();
}
