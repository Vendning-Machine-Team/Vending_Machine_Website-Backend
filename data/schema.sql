CREATE TABLE products(
    product_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL (10,2) NOT NULL,
    inventory INT DEFAULT 0 NOT NULL,
    image_url TEXT DEFAULT "../images/default.jpg"
);
CREATE TABLE action_type(
    type_id INTEGER PRIMARY KEY,
    type_name VARCHAR(20) NOT NULL
);
CREATE TABLE actions (
    action_id INTEGER PRIMARY KEY NOT NULL,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(20) REFERENCES administrators(username),
    action_type_id INT REFERENCES action_type(type_id)
);
CREATE TABLE administrators (
        username VARCHAR(20) PRIMARY KEY,
   first_name VARCHAR(50) NOT NULL,
   last_name VARCHAR (50) NOT NULL,
   password TEXT NOT NULL,
   is_active BOOLEAN DEFAULT FALSE,
   last_seen DATETIME DEFAULT NULL
);
CREATE TABLE valid_codes(
    code TEXT PRIMARY KEY,
    stripe_session_id TEXT UNIQUE,
    is_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    customer_email TEXT
    );

CREATE TRIGGER update_valid_codes AFTER INSERT ON valid_codes 
FOR EACH ROW
BEGIN 
    DELETE FROM valid_codes WHERE created_at < datetime('now', '-1 day');
    DELETE FROM valid_codes WHERE is_used = 1;
END;