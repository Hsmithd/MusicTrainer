import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import Profile from './pages/Profile';
import './App.css';

function App() {
  return (
    <div className="App">


      {/* Routes */}
      <Routes>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<Home />} />
        <Route path="/profile" element={<Profile />} />

        {/* 404 fallback */}
        <Route path="*" element={<h1>Page Not Found</h1>} />
      </Routes>
    </div>
  );
}

export default App;
