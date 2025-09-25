-- Sample SQL file for testing multi-file upload functionality
-- This file contains various SQL statements to test the processing capabilities

-- Create a users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on email for faster lookups
CREATE INDEX idx_users_email ON users(email);

-- Insert sample data
INSERT INTO users (username, email, password_hash) VALUES 
('john_doe', 'john@example.com', 'hashed_password_123'),
('jane_smith', 'jane@example.com', 'hashed_password_456'),
('admin_user', 'admin@example.com', 'hashed_password_789');

-- Create a posts table with foreign key relationship
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Query to find all published posts with user information
SELECT 
    p.id as post_id,
    p.title,
    p.content,
    u.username,
    u.email,
    p.created_at
FROM posts p
JOIN users u ON p.user_id = u.id
WHERE p.published = TRUE
ORDER BY p.created_at DESC;

-- Update user information
UPDATE users 
SET updated_at = CURRENT_TIMESTAMP 
WHERE id = 1;

-- Create a view for user statistics
CREATE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    COUNT(p.id) as total_posts,
    COUNT(CASE WHEN p.published = TRUE THEN 1 END) as published_posts
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.username;

-- Drop table if needed for cleanup
-- DROP TABLE IF EXISTS posts;
-- DROP TABLE IF EXISTS users; 