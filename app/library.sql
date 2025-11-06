BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "alembic_version" (
	"version_num"	VARCHAR(32) NOT NULL,
	CONSTRAINT "alembic_version_pkc" PRIMARY KEY("version_num")
);
CREATE TABLE IF NOT EXISTS "books" (
	"id"	INTEGER NOT NULL,
	"isbn"	VARCHAR(13),
	"title"	VARCHAR(200) NOT NULL,
	"author"	VARCHAR(200) NOT NULL,
	"publisher"	VARCHAR(200),
	"publication_year"	INTEGER,
	"edition"	VARCHAR(50),
	"language"	VARCHAR(50),
	"pages"	INTEGER,
	"description"	TEXT,
	"category_id"	INTEGER,
	"quantity"	INTEGER NOT NULL,
	"shelf_location"	VARCHAR(50),
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	PRIMARY KEY("id"),
	FOREIGN KEY("category_id") REFERENCES "categories"("id")
);
CREATE TABLE IF NOT EXISTS "categories" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(100) NOT NULL,
	"description"	TEXT,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "loans" (
	"id"	INTEGER NOT NULL,
	"book_id"	INTEGER NOT NULL,
	"member_id"	INTEGER NOT NULL,
	"borrow_date"	DATE NOT NULL,
	"due_date"	DATE NOT NULL,
	"return_date"	DATE,
	"status"	VARCHAR(8) NOT NULL,
	"notes"	TEXT,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	"fine_amount"	NUMERIC(10, 2) NOT NULL,
	"fine_paid"	NUMERIC(10, 2) NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("book_id") REFERENCES "books"("id"),
	FOREIGN KEY("member_id") REFERENCES "members"("id")
);
CREATE TABLE IF NOT EXISTS "members" (
	"id"	INTEGER NOT NULL,
	"member_id"	VARCHAR(20) NOT NULL,
	"name"	VARCHAR(100) NOT NULL,
	"email"	VARCHAR(120) NOT NULL,
	"phone"	VARCHAR(20),
	"address"	TEXT,
	"registration_date"	DATE NOT NULL,
	"status"	VARCHAR(9) NOT NULL,
	"notes"	TEXT,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL,
	"username"	VARCHAR(80) NOT NULL,
	"email"	VARCHAR(120) NOT NULL,
	"password_hash"	VARCHAR(255) NOT NULL,
	"full_name"	VARCHAR(100) NOT NULL,
	"role"	VARCHAR(9) NOT NULL,
	"is_active"	BOOLEAN,
	"created_at"	DATETIME,
	"updated_at"	DATETIME,
	PRIMARY KEY("id")
);
CREATE INDEX IF NOT EXISTS "ix_books_author" ON "books" (
	"author"
);
CREATE INDEX IF NOT EXISTS "ix_books_category_id" ON "books" (
	"category_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_books_isbn" ON "books" (
	"isbn"
);
CREATE INDEX IF NOT EXISTS "ix_books_title" ON "books" (
	"title"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_categories_name" ON "categories" (
	"name"
);
CREATE INDEX IF NOT EXISTS "ix_loans_book_id" ON "loans" (
	"book_id"
);
CREATE INDEX IF NOT EXISTS "ix_loans_member_id" ON "loans" (
	"member_id"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_members_email" ON "members" (
	"email"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_members_member_id" ON "members" (
	"member_id"
);
CREATE INDEX IF NOT EXISTS "ix_members_name" ON "members" (
	"name"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_email" ON "users" (
	"email"
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_username" ON "users" (
	"username"
);
COMMIT;
