// Calls to the Django backend's etude endpoints (backend/App/urls.py).

export async function generateEtude({ difficulty, complexity, speed }) {
    const response = await fetch('/api/generate-etude/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ difficulty, complexity, speed }),
    });
    return response.json();
}
