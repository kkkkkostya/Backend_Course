CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    first_name TEXT NOT NULL CHECK (length(btrim(first_name)) > 0),
    last_name TEXT NOT NULL CHECK (length(btrim(last_name)) > 0),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    violations_qty INTEGER NOT NULL DEFAULT 0 CHECK (violations_qty >= 0)
);

CREATE TABLE advertisements (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY CHECK (id > 0),
    seller_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL CHECK (length(btrim(name)) > 0),
    description TEXT NOT NULL CHECK (length(btrim(description)) > 0),
    category INTEGER NOT NULL CHECK (category > 0),
    images_qty INTEGER NOT NULL CHECK (images_qty >= 0)
);

CREATE INDEX advertisements_seller_id_idx ON advertisements (seller_id);
