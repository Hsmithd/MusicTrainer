import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Home.css';
import ScoreViewer from './MidiScoreViewer';
import { Wand2 } from 'lucide-react';

function Home() {
    const [abcNotation, setAbcNotation] = useState(
        "C2 C2 | G2 G2 | A2 A2 | G4 | G2 G2 | A2 A2 | G4 | G2 G2 | A2 A2 | G4 |"
    );
    const [isGenerating, setIsGenerating] = useState(false);

    // Difficulty slider states
    const [difficulty, setDifficulty] = useState(2); // 1=Easy, 2=Medium, 3=Hard
    const [complexity, setComplexity] = useState(5);
    const [speed, setSpeed] = useState(5);

    const difficultyLabel = (level) => {
        switch (Number(level)) {
            case 1: return 'Easy';
            case 2: return 'Medium';
            case 3: return 'Hard';
            default: return 'Medium';
        }
    };

    const handleGenerate = async () => {
        setIsGenerating(true);
        try {
            const response = await fetch('/api/generate-etude/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ difficulty, complexity, speed }),
            });

            const data = await response.json();

            if (data.success && data.abc_notation) {
                const tunes = data.abc_notation.split('\n\n');
                const firstTune = tunes.length > 0
                    ? tunes[0].split('\n').slice(1).join('\n')
                    : '';
                setAbcNotation(firstTune);
            } else {
                console.error('Generation failed:', data.error);
                alert('Failed to generate etude: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error generating etude:', error);
            alert('Error generating etude: ' + error.message);
        } finally {
            setIsGenerating(false);
        }
    };

    const levels = [
        { value: 1, label: 'Easy' },
        { value: 2, label: 'Medium' },
        { value: 3, label: 'Hard' },
    ];

    return (
        <div className="home-container">
            {/* Navigation Bar */}
            <nav className="navbar">
                <div className="nav-brand">
                    <span className="logo-icon">🎵</span>
                    MusicTrainer
                </div>
                <div className="nav-links">
                    <Link to="/home" className="nav-link">Home</Link>
                    <a href="#practice" className="nav-link">Ear Training</a>
                    <a href="#stats" className="nav-link">Statistics</a>
                    <Link to="/profile" className="nav-link">Profile</Link>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-content">
                    <h1 className="hero-title">Welcome to MusicTrainer</h1>
                </div>
            </section>

            {/* Score Viewer Section */}
            <section className="score-section">
                <div className="score-container">
                    {ScoreViewer ? <ScoreViewer abcNotation={abcNotation} /> : <p>Loading ScoreViewer...</p>}
                </div>
            </section>

            <section className="settings-section">
                <div className="score-actions">
                    <button
                        className={`generate-button ${isGenerating ? 'generating' : ''}`}
                        onClick={handleGenerate}
                        disabled={isGenerating}
                    >
                        <Wand2 className="generate-icon" size={20} />
                        {isGenerating ? 'Generating...' : 'Generate Etude'}
                    </button>
                </div>

                <div className="sliders">
                    <div
                        className="settings-panel"
                        style={{
                            maxWidth: 600,
                            margin: '16px auto',
                            borderRadius: 12
                        }}
                    >
                        <div className="difficulty-section" style={{ marginTop: 0, paddingTop: 0 }}>
                            <h3 className="section-title" style={{ fontSize: 18, marginBottom: 12 }}>
                                Difficulty
                            </h3>

                            <p style={{ margin: '0 0 12px 0', color: '#666', fontSize: 13 }}>
                                Select how challenging the generated etude should be.
                            </p>

                            <div className="slider-group" style={{ marginBottom: 8 }}>
                                <label htmlFor="difficulty-slider" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span>Choose level</span>
                                    <strong style={{ color: '#007acc' }}>{difficultyLabel(difficulty)}</strong>
                                </label>
                                <input
                                    id="difficulty-slider"
                                    type="range"
                                    min="1"
                                    max="3"
                                    step="1"
                                    value={difficulty}
                                    onChange={(e) => setDifficulty(Number(e.target.value))}
                                    className="difficulty-slider"
                                    aria-label="Difficulty"
                                    aria-valuemin={1}
                                    aria-valuemax={3}
                                    aria-valuenow={difficulty}
                                    aria-valuetext={difficultyLabel(difficulty)}
                                />
                            </div>

                            <div
                                aria-hidden="true"
                                style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    gap: 8,
                                    marginTop: 10
                                }}
                            >
                                {levels.map((lvl) => {
                                    const active = difficulty === lvl.value;
                                    return (
                                        <button
                                            key={lvl.value}
                                            type="button"
                                            onClick={() => setDifficulty(lvl.value)}
                                            style={{
                                                flex: 1,
                                                padding: '8px 10px',
                                                borderRadius: 999,
                                                border: `1px solid ${active ? '#007acc' : '#ddd'}`,
                                                background: active ? '#007acc' : '#f7f7f7',
                                                color: active ? '#fff' : '#333',
                                                fontWeight: 600,
                                                fontSize: 13,
                                                cursor: 'pointer',
                                                transition: 'all 0.15s ease'
                                            }}
                                        >
                                            {lvl.label}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <p>&copy; 2025 MusicTrainer. Start your musical journey today!</p>
            </footer>
        </div>
    );
}

export default Home;