import React, { useState } from 'react';
import './Profile.css';

function Profile() {
    const [username, setUsername] = useState("Hayden Smith");
    const [email, setEmail] = useState("hayden@example.com");
    const [bio, setBio] = useState("Music lover and aspiring composer.");
    const [profilePic, setProfilePic] = useState("https://via.placeholder.com/120");

    const handleSave = () => {
        alert("Profile updated!");
    };

    return (
        <div className="profile-container">
            {/* Navigation Bar */}
            <nav className="navbar">
                <div className="nav-brand">
                    <span className="logo-icon">🎵</span>
                    MusicTrainer
                </div>
                <div className="nav-links">
                    <a href="/" className="nav-link">Home</a>
                    <a href="#practice" className="nav-link">Ear Training</a>
                    <a href="#stats" className="nav-link">Statistics</a>
                    <a href="#profile" className="nav-link active">Profile</a>
                </div>
            </nav>

            {/* Profile Header */}
            <section className="profile-header">
                <img src={profilePic} alt="Profile" className="profile-pic" />
                <h1>{username}</h1>
                <p className="profile-email">{email}</p>
            </section>

            {/* Stats Section */}
            <section className="stats-section">
                <h2>Your Practice Stats</h2>
                <div className="stats-grid">
                    <div className="stat-card">
                        <h3>Sessions</h3>
                        <p>42</p>
                    </div>
                    <div className="stat-card">
                        <h3>Total Time</h3>
                        <p>18 hrs</p>
                    </div>
                    <div className="stat-card">
                        <h3>Etudes Completed</h3>
                        <p>27</p>
                    </div>
                </div>
            </section>

            {/* Settings Section */}
            <section className="settings-section">
                <h2>Profile Settings</h2>
                <div className="settings-form">
                    <label>Username</label>
                    <input value={username} onChange={(e) => setUsername(e.target.value)} />

                    <label>Email</label>
                    <input value={email} onChange={(e) => setEmail(e.target.value)} />

                    <label>Bio</label>
                    <textarea value={bio} onChange={(e) => setBio(e.target.value)} />

                    <button className="save-button" onClick={handleSave}>Save Changes</button>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <p>&copy; 2025 MusicTrainer. Start your musical journey today!</p>
            </footer>
        </div>
    );
}

export default Profile;
