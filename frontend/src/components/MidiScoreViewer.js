import React, { useState, useRef, useEffect } from 'react';
import ABCJS from 'abcjs';
import { Settings } from 'lucide-react';
import './MidiScoreViewer.css';

const TIME_SIGNATURES = [
    { numerator: 4, denominator: 4, display: "4/4" },
    { numerator: 3, denominator: 4, display: "3/4" },
    { numerator: 2, denominator: 4, display: "2/4" },
    { numerator: 6, denominator: 8, display: "6/8" },
    { numerator: 9, denominator: 8, display: "9/8" },
    { numerator: 12, denominator: 8, display: "12/8" }
];

const KEY_SIGNATURES = [
    { key: 'C', display: 'C Major', semitones: 0 },
    { key: 'G', display: 'G Major', semitones: 7 },
    { key: 'D', display: 'D Major', semitones: 2 },
    { key: 'A', display: 'A Major', semitones: 9 },
    { key: 'E', display: 'E Major', semitones: 4 },
    { key: 'F', display: 'F Major', semitones: 5 },
    { key: 'Bb', display: 'Bb Major', semitones: 10 },
    { key: 'Eb', display: 'Eb Major', semitones: 3 },
    { key: 'Am', display: 'A Minor', semitones: 9 },
    { key: 'Em', display: 'E Minor', semitones: 4 },
    { key: 'Bm', display: 'B Minor', semitones: 11 },
    { key: 'Dm', display: 'D Minor', semitones: 2 },
    { key: 'Gm', display: 'G Minor', semitones: 10 }
];

const PLAYBACK_KEYS = [
    { key: 'C', display: 'C', semitones: 0 },
    { key: 'C#', display: 'C#/Db', semitones: 1 },
    { key: 'D', display: 'D', semitones: 2 },
    { key: 'D#', display: 'D#/Eb', semitones: 3 },
    { key: 'E', display: 'E', semitones: 4 },
    { key: 'F', display: 'F', semitones: 5 },
    { key: 'F#', display: 'F#/Gb', semitones: 6 },
    { key: 'G', display: 'G', semitones: 7 },
    { key: 'G#', display: 'G#/Ab', semitones: 8 },
    { key: 'A', display: 'A', semitones: 9 },
    { key: 'A#', display: 'A#/Bb', semitones: 10 },
    { key: 'B', display: 'B', semitones: 11 }
];

const ScoreViewer = ({ abcNotation = '' }) => {
    const [timeSignature, setTimeSignature] = useState({ numerator: 4, denominator: 4 });
    const [selectedKey, setSelectedKey] = useState('C');
    const [playbackKey, setPlaybackKey] = useState('C');
    const [tempo, setTempo] = useState(120);
    const [title, setTitle] = useState('New Score');
    const [showSettings, setShowSettings] = useState(false);

    const scoreRef = useRef(null);
    const synthRef = useRef(null);
    const visualObjRef = useRef(null);
    const audioContextRef = useRef(null);
    const synthControlRef = useRef(null);
    const synthControlDiv = useRef(null);
    const currentNotationRef = useRef('');
    const currentSongIdRef = useRef(null);

    // Generate a unique song ID based on the ABC notation content
    const generateSongId = (notation) => {
        return btoa(notation).slice(0, 16);
    };

    useEffect(() => {
        updateScore();
        return () => {
            cleanup();
        };
    }, [abcNotation, timeSignature, selectedKey, tempo, title]);

    useEffect(() => {
        // Force synth recreation when playback key changes
        if (visualObjRef.current) {
            console.log("Playback key changed, recreating synth...");
            setupSynthController(true);
        }
    }, [playbackKey]);

    const cleanup = () => {
        if (synthRef.current) {
            try {
                synthRef.current.stop();
            } catch (e) {
                console.warn("Error stopping synth:", e);
            }
            synthRef.current = null;
        }
        if (synthControlRef.current) {
            synthControlRef.current = null;
        }
        if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        removeHighlights();
    };

    const cleanupSynth = () => {
        if (synthRef.current) {
            try {
                synthRef.current.stop();
            } catch (e) {
                console.warn("Error stopping synth:", e);
            }
            synthRef.current = null;
        }
        if (synthControlRef.current) {
            synthControlRef.current = null;
        }
        removeHighlights();
    };

    // Calculate transposition based on the difference between visual key and playback key
    const calculateTransposition = () => {
        const visualKeyTranspose = KEY_SIGNATURES.find((sig) => sig.key === selectedKey)?.semitones || 0;
        const playbackKeyTranspose = PLAYBACK_KEYS.find((key) => key.key === playbackKey)?.semitones || 0;

        // Calculate the difference in semitones
        let transposition = playbackKeyTranspose - visualKeyTranspose;

        // Normalize to range [-6, +6] to avoid extreme transpositions
        while (transposition > 6) transposition -= 12;
        while (transposition < -6) transposition += 12;

        console.log(`Transposition: Visual key ${selectedKey} (${visualKeyTranspose}) -> Playback key ${playbackKey} (${playbackKeyTranspose}) = ${transposition} semitones`);
        return transposition;
    };

    const updateScore = async () => {
        if (!scoreRef.current) return;
        const cleanedAbcNotation = abcNotation.replace(/%%(book|source)/g, '');

        const headerString = `X:1
T:${title}
M:${timeSignature.numerator}/${timeSignature.denominator}
L:1/8
Q:1/4=${tempo}
K:${selectedKey}
`;

        const fullNotation = headerString + (abcNotation || 'z4 |]');
        const newSongId = generateSongId(abcNotation || 'z4 |]');
        const hasNotationChanged = currentNotationRef.current !== fullNotation;
        const isNewSong = currentSongIdRef.current !== newSongId;

        currentNotationRef.current = fullNotation;
        currentSongIdRef.current = newSongId;

        try {
            const visualObj = ABCJS.renderAbc(scoreRef.current, fullNotation, {
                responsive: 'resize',
                add_classes: true,
                staffwidth: 600,
                scale: 0.8,
                wrap: {
                    minSpacing: 1.8,
                    maxSpacing: 2.7,
                    preferredMeasuresPerLine: 16
                },
                format: {
                    measurenumber: true,
                    titlefont: "Arial 16",
                    tempofont: "Arial 12",
                    annotationfont: "Arial 10",
                }
            });

            if (visualObj && visualObj.length > 0) {
                visualObjRef.current = visualObj[0];
                //make notes clickable
                const notes = scoreRef.current.querySelectorAll(".abcjs-note");
                notes.forEach((noteEl) => {
                    noteEl.style.cursor = "pointer"; // show clickable cursor
                    noteEl.addEventListener("click", () => {
                        noteEl.classList.toggle("hidden-note");
                    });
                });

                // Force synth recreation for new songs or significant changes
                if (isNewSong || hasNotationChanged) {
                    console.log("Recreating synth for", isNewSong ? "new song" : "notation change");
                    await setupSynthController(true);
                } else {
                    await setupSynthController(false);
                }
            }
        } catch (error) {
            console.error("Error rendering score:", error);
        }
    };

    const setupSynthController = async (forceRecreate = false) => {
        if (!visualObjRef.current) return;

        try {
            // Always clean up existing synth when recreating or when playback key changes
            if (forceRecreate) {
                console.log("Cleaning up existing synth...");
                cleanupSynth();

                // Clear the synth control div to remove old controls
                if (synthControlDiv.current) {
                    synthControlDiv.current.innerHTML = '';
                }
            }

            // Initialize or resume audio context
            if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
                audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioContextRef.current.state === 'suspended') {
                await audioContextRef.current.resume();
            }

            // Stop current synth if playing
            if (synthRef.current) {
                synthRef.current.stop();
            }

            // Create a new synth instance
            console.log("Creating new synth instance...");
            synthRef.current = new ABCJS.synth.CreateSynth();
            const transposition = calculateTransposition();

            console.log("Initializing synth with transposition:", transposition);
            await synthRef.current.init({
                audioContext: audioContextRef.current,
                visualObj: visualObjRef.current,
                millisecondsPerMeasure: (60000 / tempo) * timeSignature.numerator,
                options: {
                    program: 0,
                    midiTranspose: transposition,
                    qpm: tempo
                }
            });

            await synthRef.current.prime();
            console.log("Synth primed successfully");

            // Define cursor control
            const cursorControl = {
                onStart: () => {
                    removeHighlights();
                },
                onEvent: (ev) => {
                    removeHighlights();
                    if (ev.elements) {
                        ev.elements.forEach((set) => {
                            set.forEach((el) => {
                                el.classList.add("playing-note");
                            });
                        });
                    }
                    if (ev.measureStart && ev.elements && ev.elements[0] && ev.elements[0][0]) {
                        ev.elements[0][0].scrollIntoView({ block: "nearest", behavior: "smooth" });
                    }
                },
                onFinished: () => {
                    removeHighlights();
                }
            };

            // Create new synth controller
            console.log("Creating new synth controller...");
            synthControlRef.current = new ABCJS.synth.SynthController();
            synthControlRef.current.load(
                synthControlDiv.current,
                cursorControl,
                {
                    displayLoop: true,
                    displayRestart: true,
                    displayPlay: true,
                    displayProgress: true,
                    displayWarp: true
                }
            );

            // Set the tune with the new notation
            synthControlRef.current.setTune(visualObjRef.current, false, {
                qpm: tempo,
                midiTranspose: transposition
            });

            console.log("Synth controller setup complete with transposition:", transposition);

        } catch (err) {
            console.error("SynthController setup failed:", err);
            cleanupSynth();
        }
    };

    const removeHighlights = () => {
        const els = document.querySelectorAll(".playing-note");
        els.forEach((el) => el.classList.remove("playing-note"));
    };

    const handleTimeSignatureChange = (sig) => {
        setTimeSignature({
            numerator: sig.numerator,
            denominator: sig.denominator
        });
    };

    const downloadAbc = () => {
        const headerString = `X:1
T:${title}
M:${timeSignature.numerator}/${timeSignature.denominator}
L:1/8
Q:1/4=${tempo}
K:${selectedKey}
`;
        const fullNotation = headerString + (abcNotation || 'z4 |]');

        const blob = new Blob([fullNotation], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/\s+/g, '_')}.abc`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    };

    return (
        <div className="score-viewer">
            <div className="header">
                <h1 className="title">ABC Score Viewer</h1>
                <div className="controls">
                  <button
                    className="settings-button"
                    onClick={() => setShowSettings(!showSettings)}
                    title="Settings"
                  >
                    <Settings size={24} />
                  </button>

                  <button
                    className="hide-unhide-all-button"
                    onClick={() => {
                      const allNotes = scoreRef.current.querySelectorAll(".abcjs-note");
                      const areAllHidden = Array.from(allNotes).every((note) =>
                        note.classList.contains("hidden-note")
                      );

                      // Toggle visibility based on the current state of the notes
                      if (areAllHidden) {
                        allNotes.forEach((note) => note.classList.remove("hidden-note"));
                      } else {
                        allNotes.forEach((note) => note.classList.add("hidden-note"));
                      }
                    }}
                    title="Hide/Unhide All Notes"
                  >
                    Hide/Unhide All Notes
                  </button>
                </div>


            </div>

            {showSettings && (
                <div className="settings-panel">
                    <div className="setting-group">
                        <label>Title:</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="setting-input"
                        />
                    </div>
                    <div className="setting-group">
                        <label>Tempo:</label>
                        <input
                            type="number"
                            value={tempo}
                            onChange={(e) => setTempo(parseInt(e.target.value))}
                            min="40"
                            max="208"
                            className="setting-input"
                        />
                    </div>
                    <div className="setting-group">
                        <label>Time Signature:</label>
                        <select
                            value={`${timeSignature.numerator}/${timeSignature.denominator}`}
                            onChange={(e) => {
                                const [num, den] = e.target.value.split('/');
                                handleTimeSignatureChange({
                                    numerator: parseInt(num),
                                    denominator: parseInt(den)
                                });
                            }}
                            className="setting-input"
                        >
                            {TIME_SIGNATURES.map((sig) => (
                                <option key={sig.display} value={sig.display}>
                                    {sig.display}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="setting-group">
                        <label>Key:</label>
                        <select
                            value={selectedKey}
                            onChange={(e) => setSelectedKey(e.target.value)}
                            className="setting-input"
                        >
                            {KEY_SIGNATURES.map((sig) => (
                                <option key={sig.key} value={sig.key}>
                                    {sig.display}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="setting-group">
                        <label>Playback Key:</label>
                        <select
                            className="setting-input"
                            value={playbackKey}
                            onChange={(e) => setPlaybackKey(e.target.value)}
                        >
                            {PLAYBACK_KEYS.map((key) => (
                                <option key={key.key} value={key.key}>
                                    {key.display}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button onClick={downloadAbc} className="download-button">
                        Download ABC
                    </button>
                </div>
            )}

            <div ref={scoreRef} className="score-container"></div>
            <div ref={synthControlDiv} className="synth-controls"></div>
        </div>
    );
};

export default ScoreViewer;