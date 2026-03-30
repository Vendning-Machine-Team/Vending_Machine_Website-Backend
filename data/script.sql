-- CREATE TABLE administrators (
-- 	username VARCHAR(20) PRIMARY KEY,
--    first_name VARCHAR(50) NOT NULL,
--    last_name VARCHAR (50) NOT NULL,
--    password TEXT NOT NULL,
--    is_active BOOLEAN DEFAULT FALSE,
--    last_seen DATETIME DEFAULT NULL
-- );

-- CREATE TABLE products(
-- 	product_id INTEGER PRIMARY KEY,
--     name VARCHAR(100) NOT NULL,
--     price DECIMAL (10,2) NOT NULL,
--     inventory INT DEFAULT 0 NOT NULL
-- );

-- CREATE TABLE actions (
--     action_id INTEGER PRIMARY KEY NOT NULL,
--     action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     username VARCHAR(20) REFERENCES administrators(username),
--     action_type_id INT REFERENCES action_type(type_id)
-- );

-- CREATE TABLE action_type(
--     type_id INTEGER PRIMARY KEY,
--     type_name VARCHAR(20) NOT NULL
-- );

-- INSERT INTO administrators (username, first_name, last_name, password) VALUES
-- ('prince_patel1', 'Prince', 'Patel', '$2b$12$ftmkM.hhvQHrlGn.FBr.O.teTAXfTLYxViAaHjHXHlgEznH2SQNcG'), --princePassword1234
-- ('sam_machado1', 'Samantha', 'Machado', '$2b$12$XGQTm3lrsO1BbX4iU7Wp1.fuCSxn8SU8i9Hl3b8HHJYa9EKTnO9/a'), --samPassword1234
-- --('tri_nguyen1', 'Tri', 'Nguyen', 'triPassword1234'),
-- --('ad_akindale', 'Ad','Akindale', 'adPassword1234'),
-- ('Fancypants123','Samuel','Saylor','$2b$12$NzchNLqjpOo1AoSDXBFtIuux7R0oOlbY3mVE5.5mK4mHBPGl.MHtq'); --samuelPassword1234

-- INSERT INTO products (product_id, name, price, inventory) VALUES
-- (1, 'General Product', 10.0, 10);

-- INSERT INTO action_type (type_id, type_name) VALUES
-- (1, 'Set Inventory'),
-- (2, 'Set Path');

-- INSERT INTO actions (action_id, username, action_type_id) VALUES
-- (1, 'sam_machado1', 2),
-- (2, 'prince_patel1', 1);

-- CREATE TABLE valid_codes(
--     code TEXT PRIMARY KEY,
--     stripe_session_id TEXT UNIQUE,
--     is_used INTEGER DEFAULT 0,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

INSERT INTO valid_codes (code,stripe_session_id) values(2222,"nnnnn");